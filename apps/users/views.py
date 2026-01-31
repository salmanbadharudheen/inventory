from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView
from .models import User
from .forms import AdminCreationForm, UserCreationForm

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
