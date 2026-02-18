from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView, DetailView
from django.http import Http404
from django.contrib import messages
from .models import User
from .forms import AdminCreationForm, UserCreationForm
from apps.core.models import Organization
from apps.assets.models import Asset

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
        """User must be data entry, checker, senior manager, or admin"""
        user = self.request.user
        return user.is_data_entry or user.is_checker or user.is_senior_manager or user.is_superuser or user.role == User.Role.ADMIN
    
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


class DataEntryRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to ensure user is data entry"""
    def test_func(self):
        user = self.request.user
        return user.is_data_entry or user.is_superuser or user.role == User.Role.ADMIN
    
    def handle_no_permission(self):
        messages.error(self.request, "Only data entry users can create approval requests.")
        return super().handle_no_permission()

class SignUpView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

class AdminCreateView(LoginRequiredMixin, CreateView):
    """Create a user (previously 'Add Admin') — allows selecting role."""
    model = User
    form_class = UserCreationForm
    template_name = 'users/admin_form.html'
    success_url = reverse_lazy('user-list')

    def form_valid(self, form):
        # Auto-assign organization from current user when present
        if self.request.user.organization:
            form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class UserListView(LoginRequiredMixin, ListView):
    model = User
    template_name = 'users/user_list.html'
    context_object_name = 'users'

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
            # Superuser sees global stats
            context['total_users'] = User.objects.count()
            context['total_orgs'] = Organization.objects.count()
            context['total_assets'] = Asset.objects.count()
            context['admin_users'] = User.objects.filter(role=User.Role.ADMIN).count()
            context['organizations'] = Organization.objects.all()[:5]
        else:
            # Regular admin sees organization-specific stats
            org = self.request.user.organization
            if org:
                context['total_users'] = User.objects.filter(organization=org).count()
                context['total_orgs'] = 1  # Their organization only
                context['total_assets'] = Asset.objects.filter(organization=org).count()
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
            user_count=Count('users'),
            asset_count=Count('asset')
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


class AdminUserDetailView(AdminRequiredMixin, DetailView):
    """Admin panel for viewing detailed user information"""
    model = User
    template_name = 'users/admin_user_detail.html'
    context_object_name = 'detail_user'
    
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
