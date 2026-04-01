"""Views for asset approval workflows"""
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.db import transaction
from django.db import models as django_models
from django.core.files.storage import default_storage
from decimal import Decimal
from datetime import date, datetime

from .models import ApprovalRequest, ApprovalLog, Asset, generate_asset_tag
from .forms_approval import AssetApprovalRequestForm
from apps.users.views import ApprovalAccessMixin


class AdminOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to restrict access to admins only"""
    def test_func(self):
        user = self.request.user
        return user.is_superuser or (hasattr(user, 'role') and user.role == 'ADMIN')
    
    def handle_no_permission(self):
        messages.error(self.request, 'You do not have permission to access approval requests. Only administrators can manage approvals.')
        return redirect('dashboard')


class CheckerOrAdminMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow checker/senior-manager/admin users to review and approve asset requests."""

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.role in ['ADMIN', 'CHECKER', 'SENIOR_MANAGER']

    def handle_no_permission(self):
        messages.error(self.request, 'Only checker, senior manager, or admin users can perform approval actions.')
        return redirect('dashboard')


class AssetApprovalRequestCreateView(AdminOnlyMixin, CreateView):
    """Create a new asset approval request (Admin only)"""
    model = ApprovalRequest
    form_class = AssetApprovalRequestForm
    template_name = 'assets/approval_request_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        # Store the request and create the approval request
        self.object = form.save(commit=False)
        self.object.organization = self.request.user.organization
        self.object.requester = self.request.user
        self.object.request_type = ApprovalRequest.RequestType.ASSET_CREATE
        self.object.status = ApprovalRequest.Status.PENDING
        
        # Store asset details in the data JSONField
        asset_category = form.cleaned_data.get('asset_category')
        asset_department = form.cleaned_data.get('asset_department')
        self.object.data = {
            'asset_name': form.cleaned_data.get('asset_name'),
            'asset_category': asset_category.name if asset_category else '',
            'asset_description': form.cleaned_data.get('asset_description'),
            'asset_cost': str(form.cleaned_data.get('asset_cost') or 0),
            'asset_quantity': form.cleaned_data.get('asset_quantity', 1),
            'asset_reason': form.cleaned_data.get('asset_reason'),
            'asset_department': asset_department.name if asset_department else '',
            'requested_by': form.cleaned_data.get('requested_by') or (self.request.user.get_full_name() or self.request.user.username),
            'requester_name': self.request.user.get_full_name() or self.request.user.username,
        }
        
        self.object.save()
        
        messages.success(
            self.request,
            f"Asset request submitted for approval. Request ID: {self.object.id}"
        )
        
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('approval-request-list')


class ApprovalRequestListView(CheckerOrAdminMixin, ListView):
    """List approval requests for approver roles"""
    model = ApprovalRequest
    template_name = 'assets/approval_request_list.html'
    context_object_name = 'approval_requests'
    paginate_by = 20
    
    def get_queryset(self):
        # Admins see all requests in their organization
        return ApprovalRequest.objects.filter(
            organization=self.request.user.organization
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        
        context['pending_count'] = queryset.filter(
            status=ApprovalRequest.Status.PENDING
        ).count()
        context['approved_count'] = queryset.filter(
            status=ApprovalRequest.Status.APPROVED
        ).count()
        context['rejected_count'] = queryset.filter(
            status__in=[
                ApprovalRequest.Status.CHECKER_REJECTED,
                ApprovalRequest.Status.SENIOR_REJECTED,
                ApprovalRequest.Status.REJECTED
            ]
        ).count()
        
        return context


class ApprovalRequestDetailView(LoginRequiredMixin, DetailView):
    """View details of an approval request (Admin only)"""
    model = ApprovalRequest
    template_name = 'assets/approval_request_detail.html'
    context_object_name = 'approval_request'
    
    def get_queryset(self):
        user = self.request.user
        base_qs = ApprovalRequest.objects.filter(
            organization=user.organization
        )
        if user.is_superuser or user.role in ['ADMIN', 'CHECKER', 'SENIOR_MANAGER']:
            return base_qs
        return base_qs.filter(requester=user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        approval_request = self.object
        
        context['approval_logs'] = approval_request.approval_logs.all().order_by('-created_at')
        user = self.request.user
        
        # Determine if user can review based on current status and role
        context['review_mode'] = None
        if approval_request.status == ApprovalRequest.Status.PENDING:
            # Checker can do step-1 approval; Senior/Admin can directly do final approval.
            if user.is_superuser or user.role in ['ADMIN', 'SENIOR_MANAGER']:
                context['can_review'] = True
                context['approval_action'] = 'Final Approval'
                context['review_mode'] = 'FINAL_DIRECT'
            elif user.role == 'CHECKER':
                context['can_review'] = True
                context['approval_action'] = 'Checker Approval'
                context['review_mode'] = 'CHECKER_STEP'
            else:
                context['can_review'] = False
                context['approval_action'] = None
        elif approval_request.status == ApprovalRequest.Status.CHECKER_APPROVED:
            # Senior Manager can review CHECKER_APPROVED requests
            context['can_review'] = user.is_superuser or user.role in ['ADMIN', 'SENIOR_MANAGER']
            context['approval_action'] = 'Senior Manager Approval'
            context['review_mode'] = 'FINAL_AFTER_CHECKER'
        else:
            context['can_review'] = False
            context['approval_action'] = None
        
        asset_detail_rows, uploaded_files = self._build_asset_details_for_display(approval_request)
        context['asset_detail_rows'] = asset_detail_rows
        context['uploaded_files'] = uploaded_files
        
        return context

    def _build_asset_details_for_display(self, approval_request):
        """Build checker-friendly detail rows from approval payload."""
        data = approval_request.data or {}
        payload = data.get('asset_payload') or {}
        file_fields = data.get('file_fields') or {}

        if not payload:
            # Fallback for legacy request format
            fallback_rows = [
                {'label': 'Asset Name', 'value': data.get('asset_name') or '—'},
                {'label': 'Category', 'value': data.get('asset_category') or '—'},
                {'label': 'Quantity', 'value': data.get('asset_quantity') or '—'},
                {'label': 'Estimated Cost', 'value': data.get('asset_cost') or '—'},
                {'label': 'Department', 'value': data.get('asset_department') or '—'},
                {'label': 'Requested By', 'value': data.get('requested_by') or '—'},
                {'label': 'Description', 'value': data.get('asset_description') or '—'},
                {'label': 'Reason', 'value': data.get('asset_reason') or '—'},
            ]
            return fallback_rows, []

        excluded_fields = {
            'id', 'organization', 'created_by', 'asset_tag', 'custom_fields',
            'is_deleted', 'deleted_at', 'created_at', 'updated_at'
        }

        model_fields = {
            field.name: field
            for field in Asset._meta.get_fields()
            if isinstance(field, django_models.Field)
        }

        detail_rows = []
        for field_name, raw_value in payload.items():
            if field_name in excluded_fields:
                continue

            field = model_fields.get(field_name)
            if not field:
                continue

            label = str(field.verbose_name).replace('_', ' ').title()
            value = self._format_asset_field_value(field, raw_value)
            detail_rows.append({'label': label, 'value': value})

        uploaded_files = []
        for file_field_name, saved_path in file_fields.items():
            field = model_fields.get(file_field_name)
            label = str(field.verbose_name).replace('_', ' ').title() if field else file_field_name.replace('_', ' ').title()
            file_name = str(saved_path).split('/')[-1] if saved_path else '—'
            file_url = ''
            if saved_path:
                try:
                    file_url = default_storage.url(saved_path)
                except Exception:
                    file_url = ''
            uploaded_files.append({
                'label': label,
                'name': file_name,
                'url': file_url,
            })

        return detail_rows, uploaded_files

    def _format_asset_field_value(self, field, raw_value):
        """Convert raw payload values into human-friendly display values."""
        if raw_value in [None, '']:
            return '—'

        if isinstance(field, django_models.ForeignKey):
            model_cls = field.remote_field.model
            obj = model_cls.objects.filter(pk=raw_value).first()
            return str(obj) if obj else str(raw_value)

        if isinstance(field, django_models.BooleanField):
            return 'Yes' if _coerce_bool(raw_value) else 'No'

        if field.choices:
            choices_map = dict(field.flatchoices)
            return choices_map.get(raw_value, str(raw_value))

        if isinstance(field, django_models.DateField) and isinstance(raw_value, str):
            try:
                return date.fromisoformat(raw_value[:10]).strftime('%d %b %Y')
            except ValueError:
                return raw_value

        if isinstance(field, django_models.DecimalField):
            try:
                return f"{Decimal(str(raw_value)):,}"
            except Exception:
                return str(raw_value)

        return str(raw_value)



class ApprovalRequiredMixin(CheckerOrAdminMixin):
    """Approvers must be checker or admin"""


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ['1', 'true', 'yes', 'on']
    return bool(value)


def _build_asset_instance_from_request(approval_request, approver):
    """Rehydrate deferred asset payload and create one or more Asset records."""
    data = approval_request.data or {}
    payload = data.get('asset_payload', {})
    file_fields = data.get('file_fields', {})

    if not payload:
        raise ValueError('No asset payload found in this approval request.')

    allowed_fields = {
        field.name: field
        for field in Asset._meta.get_fields()
        if isinstance(field, django_models.Field)
        and not field.auto_created
        and field.name not in [
            'id', 'organization', 'created_by', 'asset_tag', 'custom_fields',
            'is_deleted', 'deleted_at', 'created_at', 'updated_at'
        ]
    }

    quantity = int(payload.get('quantity') or 1)
    quantity = max(quantity, 1)
    payload['quantity'] = 1

    created_assets = []
    with transaction.atomic():
        for _ in range(quantity):
            asset = Asset(
                organization=approval_request.organization,
                created_by=approval_request.requester or approver,
            )

            for field_name, raw_value in payload.items():
                field = allowed_fields.get(field_name)
                if not field:
                    continue

                if isinstance(field, django_models.ForeignKey):
                    if raw_value in [None, '']:
                        setattr(asset, f'{field_name}_id', None)
                    else:
                        setattr(asset, f'{field_name}_id', raw_value)
                    continue

                if raw_value in [None, '']:
                    if isinstance(field, django_models.BooleanField):
                        setattr(asset, field_name, False)
                    elif isinstance(field, (django_models.IntegerField, django_models.BigIntegerField, django_models.PositiveIntegerField, django_models.PositiveBigIntegerField)):
                        default_value = field.default if field.has_default() else (None if field.null else 0)
                        setattr(asset, field_name, default_value)
                    elif isinstance(field, django_models.DecimalField):
                        default_value = field.default if field.has_default() else (None if field.null else Decimal('0'))
                        setattr(asset, field_name, default_value)
                    else:
                        setattr(asset, field_name, None if field.null else '')
                    continue

                if isinstance(field, django_models.DecimalField):
                    setattr(asset, field_name, Decimal(str(raw_value)))
                elif isinstance(field, django_models.DateField):
                    if isinstance(raw_value, str):
                        setattr(asset, field_name, date.fromisoformat(raw_value[:10]))
                    else:
                        setattr(asset, field_name, raw_value)
                elif isinstance(field, django_models.DateTimeField):
                    if isinstance(raw_value, str):
                        setattr(asset, field_name, datetime.fromisoformat(raw_value))
                    else:
                        setattr(asset, field_name, raw_value)
                elif isinstance(field, django_models.BooleanField):
                    setattr(asset, field_name, _coerce_bool(raw_value))
                elif isinstance(field, (django_models.IntegerField, django_models.BigIntegerField, django_models.PositiveIntegerField, django_models.PositiveBigIntegerField)):
                    setattr(asset, field_name, int(raw_value))
                else:
                    setattr(asset, field_name, raw_value)

            for file_field_name, saved_path in file_fields.items():
                if file_field_name in allowed_fields:
                    setattr(asset, file_field_name, saved_path)

            if not asset.category_id:
                raise ValueError('Asset category is required to create inventory record.')

            asset.asset_tag = generate_asset_tag(
                approval_request.organization,
                asset.category,
                asset.company
            )
            asset.save()
            created_assets.append(asset)

    return created_assets


class ApprovalRequestApproveView(ApprovalRequiredMixin, DetailView):
    """Approve an asset request - Checker or Senior Manager"""
    model = ApprovalRequest
    
    def post(self, request, pk):
        approval_request = get_object_or_404(
            ApprovalRequest,
            pk=pk,
            organization=request.user.organization
        )
        
        comments = request.POST.get('comments', '')
        user = request.user

        def finalize_approval(final_approver):
            created_count = 0
            if approval_request.request_type == ApprovalRequest.RequestType.ASSET_CREATE and approval_request.asset is None:
                try:
                    created_assets = _build_asset_instance_from_request(approval_request, final_approver)
                    created_count = len(created_assets)
                    if created_assets:
                        approval_request.asset = created_assets[0]
                except Exception as exc:
                    messages.error(request, f'Unable to create inventory record from request: {exc}')
                    return None

            approval_request.status = ApprovalRequest.Status.APPROVED
            approval_request.save(update_fields=['status', 'asset', 'updated_at'])

            ApprovalLog.objects.create(
                approval_request=approval_request,
                approver=final_approver,
                decision=ApprovalLog.Decision.APPROVED,
                approval_level='SENIOR_MANAGER',
                comments=comments
            )
            return created_count
        
        # Determine approval level and next status
        if approval_request.status == ApprovalRequest.Status.PENDING:
            # Senior/Admin can directly perform final approval from PENDING.
            if user.is_superuser or user.role in ['ADMIN', 'SENIOR_MANAGER']:
                created_count = finalize_approval(user)
                if created_count is None:
                    return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))

                if created_count > 0:
                    messages.success(request, f'Request fully approved. {created_count} asset(s) added to inventory.')
                else:
                    messages.success(request, 'Request has been fully approved.')
                return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))

            # Checker approval (first step)
            if user.role == 'CHECKER':
                approval_request.status = ApprovalRequest.Status.CHECKER_APPROVED
                approval_request.save(update_fields=['status', 'updated_at'])
                
                ApprovalLog.objects.create(
                    approval_request=approval_request,
                    approver=user,
                    decision=ApprovalLog.Decision.APPROVED,
                    approval_level='CHECKER',
                    comments=comments
                )
                
                messages.success(request, 'Request approved by Checker. Awaiting Senior Manager/Admin final approval.')
                return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))

            messages.error(request, 'You do not have permission to approve this request.')
            return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))
            
        elif approval_request.status == ApprovalRequest.Status.CHECKER_APPROVED:
            # Senior Manager approval (second step - final)
            if not (user.is_superuser or user.role in ['ADMIN', 'SENIOR_MANAGER']):
                messages.error(request, 'Only Senior Managers can perform final approval.')
                return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))

            created_count = finalize_approval(user)
            if created_count is None:
                return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))
            
            if created_count > 0:
                messages.success(request, f'Request fully approved. {created_count} asset(s) added to inventory.')
            else:
                messages.success(request, 'Request has been fully approved.')
            return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))
        
        else:
            messages.error(request, 'This request cannot be approved at this stage.')
            return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))


class ApprovalRequestRejectView(ApprovalRequiredMixin, DetailView):
    """Reject an asset request - Checker or Senior Manager"""
    model = ApprovalRequest
    
    def post(self, request, pk):
        approval_request = get_object_or_404(
            ApprovalRequest,
            pk=pk,
            organization=request.user.organization
        )
        
        comments = request.POST.get('comments', '')
        user = request.user
        
        if not comments:
            messages.error(request, 'Please provide a reason for rejection.')
            return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))
        
        # Determine rejection level
        if approval_request.status == ApprovalRequest.Status.PENDING:
            # Senior/Admin can directly do final rejection from pending.
            if user.is_superuser or user.role in ['ADMIN', 'SENIOR_MANAGER']:
                approval_request.status = ApprovalRequest.Status.SENIOR_REJECTED
                approval_level = 'SENIOR_MANAGER'
            elif user.role == 'CHECKER':
                approval_request.status = ApprovalRequest.Status.CHECKER_REJECTED
                approval_level = 'CHECKER'
            else:
                messages.error(request, 'You do not have permission to reject this request.')
                return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))
            
        elif approval_request.status == ApprovalRequest.Status.CHECKER_APPROVED:
            # Senior Manager rejection
            if not (user.is_superuser or user.role in ['ADMIN', 'SENIOR_MANAGER']):
                messages.error(request, 'Only Senior Managers can reject at this stage.')
                return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))
            
            approval_request.status = ApprovalRequest.Status.SENIOR_REJECTED
            approval_level = 'SENIOR_MANAGER'
        else:
            messages.error(request, 'This request cannot be rejected at this stage.')
            return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))

        approval_request.save(update_fields=['status', 'updated_at'])

        ApprovalLog.objects.create(
            approval_request=approval_request,
            approver=user,
            decision=ApprovalLog.Decision.REJECTED,
            approval_level=approval_level,
            comments=comments
        )

        messages.warning(request, f'Request has been rejected by {approval_level.replace("_", " ").title()}.')
        return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))


class ApprovalPendingListView(ApprovalRequiredMixin, ListView):
    """List pending approval requests for the current approver"""
    model = ApprovalRequest
    template_name = 'assets/approval_pending_list.html'
    context_object_name = 'pending_requests'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        base_qs = ApprovalRequest.objects.filter(
            organization=user.organization
        )
        
        # Checkers see PENDING requests
        if user.role == 'CHECKER' and not user.is_superuser:
            return base_qs.filter(
                status=ApprovalRequest.Status.PENDING
            ).order_by('-created_at')
        
        # Senior Managers can final-approve CHECKER_APPROVED and can directly approve PENDING.
        if user.role == 'SENIOR_MANAGER' and not user.is_superuser:
            return base_qs.filter(
                status__in=[ApprovalRequest.Status.PENDING, ApprovalRequest.Status.CHECKER_APPROVED]
            ).order_by('-created_at')
        
        # Admins and superusers see both PENDING and CHECKER_APPROVED
        return base_qs.filter(
            status__in=[ApprovalRequest.Status.PENDING, ApprovalRequest.Status.CHECKER_APPROVED]
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Count pending for current user's role
        if user.role == 'CHECKER' and not user.is_superuser:
            context['total_pending'] = ApprovalRequest.objects.filter(
                organization=user.organization,
                status=ApprovalRequest.Status.PENDING
            ).count()
            context['approval_stage'] = 'Checker'
        elif user.role == 'SENIOR_MANAGER' and not user.is_superuser:
            context['total_pending'] = ApprovalRequest.objects.filter(
                organization=user.organization,
                status__in=[ApprovalRequest.Status.PENDING, ApprovalRequest.Status.CHECKER_APPROVED]
            ).count()
            context['approval_stage'] = 'Senior Manager'
        else:
            # Admins see combined count
            pending_count = ApprovalRequest.objects.filter(
                organization=user.organization,
                status=ApprovalRequest.Status.PENDING
            ).count()
            checker_approved_count = ApprovalRequest.objects.filter(
                organization=user.organization,
                status=ApprovalRequest.Status.CHECKER_APPROVED
            ).count()
            context['total_pending'] = pending_count + checker_approved_count
            context['checker_pending_count'] = pending_count
            context['senior_pending_count'] = checker_approved_count
            context['approval_stage'] = 'All'
        
        return context
