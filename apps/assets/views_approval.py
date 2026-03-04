"""Views for asset approval workflows"""
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.urls import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.utils import timezone

from .models import ApprovalRequest, ApprovalLog
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


class ApprovalRequestListView(AdminOnlyMixin, ListView):
    """List all approval requests (Admin only)"""
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


class ApprovalRequestDetailView(AdminOnlyMixin, DetailView):
    """View details of an approval request (Admin only)"""
    model = ApprovalRequest
    template_name = 'assets/approval_request_detail.html'
    context_object_name = 'approval_request'
    
    def get_queryset(self):
        return ApprovalRequest.objects.filter(
            organization=self.request.user.organization
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        approval_request = self.object
        
        context['approval_logs'] = approval_request.approval_logs.all().order_by('-created_at')
        context['is_admin'] = True  # Only admins can access this view
        
        return context



class ApprovalRequiredMixin(AdminOnlyMixin):
    """Alias for AdminOnlyMixin - approvers must be admins"""


class ApprovalRequestApproveView(ApprovalRequiredMixin, DetailView):
    """Approve an asset request"""
    model = ApprovalRequest
    
    def post(self, request, pk):
        approval_request = get_object_or_404(
            ApprovalRequest,
            pk=pk,
            organization=request.user.organization
        )
        
        comments = request.POST.get('comments', '')
        user_role = getattr(request.user, 'role', 'ADMIN')
        
        # Determine approval flow
        if approval_request.status == ApprovalRequest.Status.PENDING:
            # First approval (Checker)
            approval_request.status = ApprovalRequest.Status.CHECKER_APPROVED
            log_action = 'Checker Approved'
            approval_level = 'CHECKER'
        elif approval_request.status == ApprovalRequest.Status.CHECKER_APPROVED:
            # Second approval (Senior Manager)
            approval_request.status = ApprovalRequest.Status.APPROVED
            log_action = 'Senior Manager Approved'
            approval_level = 'SENIOR_MANAGER'
        else:
            messages.error(request, 'This request cannot be approved at this stage.')
            return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))
        
        approval_request.save()
        
        # Create approval log
        ApprovalLog.objects.create(
            approval_request=approval_request,
            approver=request.user,
            decision=ApprovalLog.Decision.APPROVED,
            approval_level=approval_level,
            comments=comments
        )
        
        messages.success(request, f'Request has been approved. ({log_action})')
        return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))


class ApprovalRequestRejectView(ApprovalRequiredMixin, DetailView):
    """Reject an asset request"""
    model = ApprovalRequest
    
    def post(self, request, pk):
        approval_request = get_object_or_404(
            ApprovalRequest,
            pk=pk,
            organization=request.user.organization
        )
        
        comments = request.POST.get('comments', '')
        
        if not comments:
            messages.error(request, 'Please provide a reason for rejection.')
            return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))
        
        # Determine rejection type
        if approval_request.status == ApprovalRequest.Status.PENDING:
            approval_request.status = ApprovalRequest.Status.CHECKER_REJECTED
            log_action = 'Checker Rejected'
            approval_level = 'CHECKER'
        elif approval_request.status == ApprovalRequest.Status.CHECKER_APPROVED:
            approval_request.status = ApprovalRequest.Status.SENIOR_REJECTED
            log_action = 'Senior Manager Rejected'
            approval_level = 'SENIOR_MANAGER'
        else:
            messages.error(request, 'This request cannot be rejected at this stage.')
            return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))
        
        approval_request.save()
        
        # Create approval log
        ApprovalLog.objects.create(
            approval_request=approval_request,
            approver=request.user,
            decision=ApprovalLog.Decision.REJECTED,
            approval_level=approval_level,
            comments=comments
        )
        
        messages.warning(request, f'Request has been rejected. ({log_action})')
        return HttpResponseRedirect(reverse('approval-request-detail', args=[pk]))


class ApprovalPendingListView(ApprovalRequiredMixin, ListView):
    """List pending approval requests for the current approver"""
    model = ApprovalRequest
    template_name = 'assets/approval_pending_list.html'
    context_object_name = 'pending_requests'
    paginate_by = 20
    
    def get_queryset(self):
        user_role = getattr(self.request.user, 'role', 'ADMIN')
        
        if user_role in ['CHECKER', 'ADMIN']:
            # Checkers see pending requests
            return ApprovalRequest.objects.filter(
                organization=self.request.user.organization,
                status=ApprovalRequest.Status.PENDING
            ).order_by('-created_at')
        elif user_role == 'SENIOR_MANAGER':
            # Senior managers see checker-approved requests
            return ApprovalRequest.objects.filter(
                organization=self.request.user.organization,
                status=ApprovalRequest.Status.CHECKER_APPROVED
            ).order_by('-created_at')
        
        return ApprovalRequest.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context['total_pending'] = queryset.count()
        return context
