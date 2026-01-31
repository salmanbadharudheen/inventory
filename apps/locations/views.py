from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Branch, Department, Building, Floor, Room
from .forms import BranchForm, DepartmentForm, BuildingForm, FloorForm, RoomForm

# --- BRANCH VIEWS ---
class BranchListView(LoginRequiredMixin, ListView):
    model = Branch
    template_name = 'locations/branch_list.html'
    context_object_name = 'branches'

    def get_queryset(self):
        return Branch.objects.filter(organization=self.request.user.organization)

class BranchCreateView(LoginRequiredMixin, CreateView):
    model = Branch
    form_class = BranchForm
    template_name = 'locations/branch_form.html'
    success_url = reverse_lazy('branch-list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class BranchUpdateView(LoginRequiredMixin, UpdateView):
    model = Branch
    form_class = BranchForm
    template_name = 'locations/branch_form.html'
    success_url = reverse_lazy('branch-list')

    def get_queryset(self):
        return Branch.objects.filter(organization=self.request.user.organization)

# --- DEPARTMENT VIEWS ---
class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'locations/department_list.html'
    context_object_name = 'departments'

    def get_queryset(self):
        return Department.objects.filter(organization=self.request.user.organization).select_related('branch')

class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'locations/department_form.html'
    success_url = reverse_lazy('department-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'locations/department_form.html'
    success_url = reverse_lazy('department-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_queryset(self):
        return Department.objects.filter(organization=self.request.user.organization)

# --- BUILDING VIEWS ---
class BuildingListView(LoginRequiredMixin, ListView):
    model = Building
    template_name = 'locations/building_list.html'
    context_object_name = 'buildings'

    def get_queryset(self):
        return Building.objects.filter(organization=self.request.user.organization).select_related('branch')

class BuildingCreateView(LoginRequiredMixin, CreateView):
    model = Building
    form_class = BuildingForm
    template_name = 'locations/building_form.html'
    success_url = reverse_lazy('building-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

# --- FLOOR VIEWS ---
class FloorListView(LoginRequiredMixin, ListView):
    model = Floor
    template_name = 'locations/floor_list.html'
    context_object_name = 'floors'

    def get_queryset(self):
        return Floor.objects.filter(organization=self.request.user.organization).select_related('building')

class FloorCreateView(LoginRequiredMixin, CreateView):
    model = Floor
    form_class = FloorForm
    template_name = 'locations/floor_form.html'
    success_url = reverse_lazy('floor-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

# --- ROOM VIEWS ---
class RoomListView(LoginRequiredMixin, ListView):
    model = Room
    template_name = 'locations/room_list.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        return Room.objects.filter(organization=self.request.user.organization).select_related('floor')

class RoomCreateView(LoginRequiredMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'locations/room_form.html'
    success_url = reverse_lazy('room-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)
