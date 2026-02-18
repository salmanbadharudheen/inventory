from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, TemplateView
from .models import User
from .forms import AdminCreationForm, UserCreationForm
from apps.core.models import Organization
from apps.assets.models import Asset

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to check if user is superuser or admin"""
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == User.Role.ADMIN

class SignUpView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('login')

class AdminCreateView(LoginRequiredMixin, CreateView):
    model = User
    form_class = AdminCreationForm
    template_name = 'users/admin_form.html'
    success_url = reverse_lazy('user-list')

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        # Add permission check logic here later (e.g., only superusers or existing admins can create admins)

    def form_valid(self, form):
        # We can auto-assign organization from current user if needed:
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
        qs = User.objects.all().select_related('organization', 'branch', 'department')
        
        # If not superuser, filter to their organization only
        if not self.request.user.is_superuser and self.request.user.organization:
            qs = qs.filter(organization=self.request.user.organization)
        
        # Filter by search query if provided
        search = self.request.GET.get('q', '')
        if search:
            qs = qs.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        return qs.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
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
