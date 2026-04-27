from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, ListView, TemplateView, DetailView, UpdateView, DeleteView, FormView, View
from django.http import Http404, JsonResponse
from django.contrib import messages
from .models import User
from .forms import AdminCreationForm, UserCreationForm, OrganizationForm, AssignOrganizationAdminForm, OrganizationCreateWithAdminForm
from apps.core.models import Organization
from apps.assets.models import Asset


def is_superuser_org_mode(request):
    return bool(
        request.user.is_authenticated
        and request.user.is_superuser
        and request.session.get('superuser_org_mode')
        and request.user.organization_id
    )

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to check if user is superuser or admin"""
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == User.Role.ADMIN
    
    def handle_no_permission(self):
        """Handle when user doesn't have permission"""
        messages.error(self.request, "You don't have permission to access this page. Admin or Superuser access required.")
        return super().handle_no_permission()


class ApprovalAccessMixin(LoginRequiredMixin):
    """Mixin to ensure user has approval workflow access"""
    def test_func(self):
        """User must be employee, checker, senior manager, or admin"""
        user = self.request.user
        return (user.role == User.Role.EMPLOYEE) or user.is_checker or user.is_senior_manager or user.is_superuser or user.role == User.Role.ADMIN
    
    def handle_no_permission(self):
        messages.error(self.request, "You don't have permission to access approval workflows.")
        return super().handle_no_permission()


class CheckerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user is a checker"""
    def test_func(self):
        user = self.request.user
        return user.is_checker or user.is_superuser or user.role == User.Role.ADMIN
    
    def handle_no_permission(self):
        messages.error(self.request, "Only checkers can perform this action.")
        return super().handle_no_permission()


class SeniorManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user is a senior manager"""
    def test_func(self):
        user = self.request.user
        return user.is_senior_manager or user.is_superuser or user.role == User.Role.ADMIN
    
    def handle_no_permission(self):
        messages.error(self.request, "Only senior managers can perform this action.")
        return super().handle_no_permission()


class EmployeeRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user is employee"""
    def test_func(self):
        user = self.request.user
        return (user.role == User.Role.EMPLOYEE) or user.is_superuser or user.role == User.Role.ADMIN

    def handle_no_permission(self):
        messages.error(self.request, "Only employees can create approval requests.")
        return super().handle_no_permission()

class SignUpView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')


class OwnerLoginView(View):
    """Dedicated login page for the software owner (superuser only)."""
    template_name = 'owner/login.html'

    def get(self, request):
        if request.user.is_authenticated and request.user.is_superuser:
            return redirect('admin-dashboard')
        from django.shortcuts import render
        return render(request, self.template_name)

    def post(self, request):
        from django.shortcuts import render
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, self.template_name, {'error': 'Invalid username or password.'})

        if not user.is_superuser:
            return render(request, self.template_name, {
                'error': 'This portal is for the software owner only. Regular users should log in at the main portal.'
            })

        auth_login(request, user)
        return redirect('admin-dashboard')


class OwnerLogoutView(View):
    """Logout owner and redirect to owner login page."""
    def post(self, request):
        auth_logout(request)
        return redirect('owner-login')

    def get(self, request):
        auth_logout(request)
        return redirect('owner-login')


class OwnerExitOrgModeView(LoginRequiredMixin, View):
    """Exit organization viewing mode and return to owner portal."""

    def get(self, request):
        if not request.user.is_superuser:
            messages.error(request, 'Only software owner can perform this action.')
            return redirect('dashboard')

        request.session.pop('superuser_org_mode', None)
        request.user.organization = None
        request.user.save(update_fields=['organization'])
        messages.success(request, 'Exited organization mode. Back to owner portal.')
        return redirect('admin-orgs')

    def post(self, request):
        return self.get(request)


class AdminOrgLoginView(LoginRequiredMixin, View):
    """Switch superuser into selected organization context for data viewing."""

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, 'Only software owner can perform this action.')
            return redirect('dashboard')
        organization = get_object_or_404(Organization, pk=kwargs.get('pk'))
        if not organization.is_active:
            messages.error(request, f'"{organization.name}" is inactive. Activate it before entering organization mode.')
            return redirect('admin-orgs')
        request.user.organization = organization
        request.user.save(update_fields=['organization'])
        request.session['superuser_org_mode'] = True
        messages.success(request, f'Now viewing data as organization: {organization.name}')
        return redirect('dashboard')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)


class AdminCreateView(LoginRequiredMixin, CreateView):
    """Create a user (previously 'Add Admin') — allows selecting role."""
    model = User
    form_class = UserCreationForm
    template_name = 'users/admin_form.html'
    success_url = reverse_lazy('user-list')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser and not is_superuser_org_mode(request):
            messages.info(request, 'Software owner can only manage organizations from the owner portal.')
            return redirect('admin-orgs')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['current_user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Auto-assign organization from current user when present
        if self.request.user.organization:
            form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser and not is_superuser_org_mode(request):
            messages.info(request, 'Software owner can only manage organizations from the owner portal.')
            return redirect('admin-orgs')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = super().get_queryset()
        # Filter by organization if applicable
        if self.request.user.organization:
            qs = qs.filter(organization=self.request.user.organization)
        return qs


class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """Admin panel dashboard with statistics"""
    template_name = 'users/admin_dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_superuser:
            # Owner dashboard is organization-control only.
            context['owner_org_only'] = True
            context['total_orgs'] = Organization.objects.count()
            context['active_orgs'] = Organization.objects.filter(is_active=True).count()
            context['inactive_orgs'] = Organization.objects.filter(is_active=False).count()
            context['organizations'] = Organization.objects.only('id', 'name', 'slug', 'created_at')[:5]
        else:
            # Regular admin sees organization-specific stats
            org = self.request.user.organization
            if org:
                context['total_users'] = User.objects.filter(organization=org).count()
                context['total_orgs'] = 1  # Their organization only
                context['total_assets'] = Asset.objects.filter(organization=org, is_deleted=False).count()
                context['admin_users'] = User.objects.filter(
                    organization=org, 
                    role=User.Role.ADMIN
                ).count()
                context['organizations'] = [org]
        
        return context


class AdminUserListView(AdminRequiredMixin, ListView):
    """Admin panel for viewing all users"""
    model = User
    template_name = 'users/admin_user_list.html'
    context_object_name = 'users'
    paginate_by = 50

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser and not is_superuser_org_mode(request):
            messages.info(request, 'Software owner can only manage organizations from the owner portal.')
            return redirect('admin-orgs')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        qs = User.objects.all().select_related('organization', 'branch', 'department').order_by('-date_joined')
        
        # If not superuser, filter to their organization only
        if not self.request.user.is_superuser and self.request.user.organization:
            qs = qs.filter(organization=self.request.user.organization)
        
        # Filter by search query if provided
        search = self.request.GET.get('q', '').strip()
        if search:
            qs = qs.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['total_users'] = self.get_queryset().count()
        return context


class AdminOrgListView(AdminRequiredMixin, ListView):
    """Admin panel for viewing all organizations"""
    model = Organization
    template_name = 'users/admin_org_list.html'
    context_object_name = 'organizations'
    paginate_by = 50
    
    def get_queryset(self):
        qs = Organization.objects.annotate(
            user_count=Count('users', distinct=True),
            asset_count=Count('asset', filter=Q(asset__is_deleted=False), distinct=True)
        ).order_by('-created_at')
        
        # If not superuser, only show their organization
        if not self.request.user.is_superuser and self.request.user.organization:
            qs = qs.filter(id=self.request.user.organization.id)
        
        # Filter by search query if provided
        search = self.request.GET.get('q', '')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) |
                Q(slug__icontains=search)
            )
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse('owner-login'))
        messages.error(self.request, "Only the software owner can access this page.")
        return redirect(reverse('admin-dashboard'))


class AdminOrgCreateView(SuperuserRequiredMixin, CreateView):
    model = Organization
    form_class = OrganizationCreateWithAdminForm
    template_name = 'users/admin_org_form.html'
    success_url = reverse_lazy('admin-orgs')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Organization "{self.object.name}" created successfully.')
        return response


class AdminOrgUpdateView(SuperuserRequiredMixin, UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'users/admin_org_form.html'
    success_url = reverse_lazy('admin-orgs')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Organization "{self.object.name}" updated successfully.')
        return response


class AdminOrgDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Organization
    template_name = 'users/admin_org_delete_confirm.html'
    success_url = reverse_lazy('admin-orgs')

    def post(self, request, *args, **kwargs):
        org = self.get_object()
        user_count = User.objects.filter(organization=org).count()
        asset_count = Asset.objects.filter(organization=org, is_deleted=False).count()

        # Safety guard: do not allow deleting client organizations that already have data.
        if user_count > 0 or asset_count > 0:
            messages.error(
                request,
                f'Cannot delete "{org.name}" because it has {user_count} user(s) and {asset_count} asset(s).',
            )
            return redirect('admin-orgs')

        messages.success(request, f'Organization "{org.name}" deleted successfully.')
        return super().post(request, *args, **kwargs)


class AdminOrgToggleStatusView(SuperuserRequiredMixin, View):
    """Toggle organization active/inactive status."""

    def post(self, request, *args, **kwargs):
        organization = get_object_or_404(Organization, pk=kwargs.get('pk'))
        organization.is_active = not organization.is_active
        organization.save(update_fields=['is_active'])

        state = 'active' if organization.is_active else 'inactive'
        messages.success(request, f'Organization "{organization.name}" is now {state}.')
        return redirect('admin-orgs')


class AdminOrgAssignAdminView(SuperuserRequiredMixin, FormView):
    form_class = AssignOrganizationAdminForm
    template_name = 'users/admin_org_assign_admin.html'

    def dispatch(self, request, *args, **kwargs):
        self.organization = get_object_or_404(Organization, pk=kwargs.get('pk'))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['org'] = self.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['org'] = self.organization
        context['current_admins'] = User.objects.filter(
            organization=self.organization,
            role=User.Role.ADMIN,
        ).order_by('username')
        return context

    def form_valid(self, form):
        mode = form.cleaned_data.get('mode')
        
        if mode == 'existing':
            # Assign existing user as admin
            user = form.cleaned_data['user']
            user.organization = self.organization
            user.role = User.Role.ADMIN
            user.is_superuser = False
            user.save(update_fields=['organization', 'role', 'is_superuser'])
            messages.success(self.request, f'User "{user.username}" is now an admin for "{self.organization.name}".')
        else:  # mode == 'create'
            # Create new admin user (form.save() handles this)
            user = form.save(commit=True)
            messages.success(self.request, f'New admin user "{user.username}" has been created for "{self.organization.name}".')
        
        return redirect('admin-org-dashboard', pk=self.organization.pk)


class AdminOrgDashboardView(SuperuserRequiredMixin, DetailView):
    """Owner-facing single organization dashboard."""
    model = Organization
    template_name = 'users/admin_org_dashboard.html'
    context_object_name = 'org'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.get_object()
        context['total_users'] = User.objects.filter(organization=org).count()
        context['admin_users'] = User.objects.filter(organization=org, role=User.Role.ADMIN).count()
        context['total_assets'] = Asset.objects.filter(organization=org, is_deleted=False).count()
        context['recent_admins'] = User.objects.filter(
            organization=org,
            role=User.Role.ADMIN,
        ).order_by('-date_joined')[:8]
        return context


class AdminUserDetailView(AdminRequiredMixin, DetailView):
    """Admin panel for viewing detailed user information"""
    model = User
    template_name = 'users/admin_user_detail.html'
    context_object_name = 'detail_user'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_superuser and not is_superuser_org_mode(request):
            messages.info(request, 'Software owner can only manage organizations from the owner portal.')
            return redirect('admin-orgs')
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        qs = User.objects.select_related('organization', 'branch', 'department')
        
        # If not superuser, only allow viewing users in their organization
        if not self.request.user.is_superuser and self.request.user.organization:
            qs = qs.filter(organization=self.request.user.organization)
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Get user's assets if applicable
        user_obj = self.get_object()
        context['assigned_assets'] = Asset.objects.filter(
            assigned_to=user_obj
        ).select_related('category', 'organization')[:10]
        return context


class OrgAssetTagSettingsView(SuperuserRequiredMixin, DetailView):
    """Organization asset tag configuration – superuser only."""
    model = Organization
    template_name = 'users/org_tag_settings.html'
    context_object_name = 'org'

    def post(self, request, *args, **kwargs):
        org = self.get_object()
        org.tag_prefix = request.POST.get('tag_prefix', '').strip()[:20]
        org.tag_separator = request.POST.get('tag_separator', '-').strip()[:5] or '-'
        org.tag_include_company = request.POST.get('tag_include_company') == 'on'
        org.tag_include_category = request.POST.get('tag_include_category') == 'on'
        org.tag_include_year = request.POST.get('tag_include_year') == 'on'
        seq = request.POST.get('tag_sequence_format', 'HEX4')
        if seq in dict(Organization.SequenceFormat.choices):
            org.tag_sequence_format = seq
        lbl = request.POST.get('label_template', 'CLASSIC')
        if lbl in dict(Organization.LabelTemplate.choices):
            org.label_template = lbl
        org.save()
        messages.success(request, f"Asset tag settings for '{org.name}' saved successfully.")
        return redirect(reverse('org-tag-settings', kwargs={'pk': org.pk}))

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['sequence_choices'] = Organization.SequenceFormat.choices
        ctx['label_choices'] = Organization.LabelTemplate.choices
        ctx['tag_preview'] = self.get_object().get_tag_preview()
        return ctx


class OrgTagPreviewAPI(SuperuserRequiredMixin, DetailView):
    """Return a live tag preview as JSON – called via fetch()."""
    model = Organization

    def get(self, request, *args, **kwargs):
        org = self.get_object()
        # Temporarily apply params from query string for preview
        org.tag_prefix = request.GET.get('tag_prefix', org.tag_prefix or '')
        org.tag_separator = request.GET.get('tag_separator', org.tag_separator or '-') or '-'
        org.tag_include_company = request.GET.get('tag_include_company', '1') == '1'
        org.tag_include_category = request.GET.get('tag_include_category', '1') == '1'
        org.tag_include_year = request.GET.get('tag_include_year', '1') == '1'
        org.tag_sequence_format = request.GET.get('tag_sequence_format', org.tag_sequence_format or 'HEX4')
        return JsonResponse({'preview': org.get_tag_preview()})
