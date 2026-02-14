from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Branch, Department, Building, Floor, Room, Region, Site, Location, SubLocation
from .forms import (BranchForm, DepartmentForm, BuildingForm, FloorForm, RoomForm,
                    RegionForm, SiteForm, LocationForm, SubLocationForm)
from django.http import JsonResponse

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

# --- REGION VIEWS ---
class RegionListView(LoginRequiredMixin, ListView):
    model = Region
    template_name = 'locations/region_list.html'
    context_object_name = 'regions'

    def get_queryset(self):
        return Region.objects.filter(organization=self.request.user.organization)

class RegionCreateView(LoginRequiredMixin, CreateView):
    model = Region
    form_class = RegionForm
    template_name = 'locations/region_form.html'
    success_url = reverse_lazy('region-list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class RegionUpdateView(LoginRequiredMixin, UpdateView):
    model = Region
    form_class = RegionForm
    template_name = 'locations/region_form.html'
    success_url = reverse_lazy('region-list')

    def get_queryset(self):
        return Region.objects.filter(organization=self.request.user.organization)

# --- SITE VIEWS ---
class SiteListView(LoginRequiredMixin, ListView):
    model = Site
    template_name = 'locations/site_list.html'
    context_object_name = 'sites'

    def get_queryset(self):
        return Site.objects.filter(region__organization=self.request.user.organization).select_related('region')

class SiteCreateView(LoginRequiredMixin, CreateView):
    model = Site
    form_class = SiteForm
    template_name = 'locations/site_form.html'
    success_url = reverse_lazy('site-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def form_valid(self, form):
        # organization is inherited via region in a way, but we might need it on region
        return super().form_valid(form)

class SiteUpdateView(LoginRequiredMixin, UpdateView):
    model = Site
    form_class = SiteForm
    template_name = 'locations/site_form.html'
    success_url = reverse_lazy('site-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_queryset(self):
        return Site.objects.filter(region__organization=self.request.user.organization)

# --- LOCATION VIEWS ---
class LocationListView(LoginRequiredMixin, ListView):
    model = Location
    template_name = 'locations/location_list.html'
    context_object_name = 'locations_list'

    def get_queryset(self):
        return Location.objects.filter(site__region__organization=self.request.user.organization).select_related('site', 'building')

class LocationCreateView(LoginRequiredMixin, CreateView):
    model = Location
    form_class = LocationForm
    template_name = 'locations/location_form.html'
    success_url = reverse_lazy('location-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

class LocationUpdateView(LoginRequiredMixin, UpdateView):
    model = Location
    form_class = LocationForm
    template_name = 'locations/location_form.html'
    success_url = reverse_lazy('location-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_queryset(self):
        return Location.objects.filter(site__region__organization=self.request.user.organization)

# --- SUBLOCATION VIEWS ---
class SubLocationListView(LoginRequiredMixin, ListView):
    model = SubLocation
    template_name = 'locations/sublocation_list.html'
    context_object_name = 'sublocations'

    def get_queryset(self):
        return SubLocation.objects.filter(location__site__region__organization=self.request.user.organization).select_related('location')

class SubLocationCreateView(LoginRequiredMixin, CreateView):
    model = SubLocation
    form_class = SubLocationForm
    template_name = 'locations/sublocation_form.html'
    success_url = reverse_lazy('sublocation-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

class SubLocationUpdateView(LoginRequiredMixin, UpdateView):
    model = SubLocation
    form_class = SubLocationForm
    template_name = 'locations/sublocation_form.html'
    success_url = reverse_lazy('sublocation-list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

    def get_queryset(self):
        return SubLocation.objects.filter(location__site__region__organization=self.request.user.organization)

# AJAX Endpoints for Location Hierarchy
def get_sites(request):
    region_id = request.GET.get('region_id')
    if region_id:
        sites = Site.objects.filter(region_id=region_id).values('id', 'name')
        return JsonResponse(list(sites), safe=False)
    return JsonResponse([], safe=False)

def get_locations(request):
    site_id = request.GET.get('site_id')
    if site_id:
        locations = Location.objects.filter(site_id=site_id).values('id', 'name')
        return JsonResponse(list(locations), safe=False)
    return JsonResponse([], safe=False)

def get_sublocations(request):
    location_id = request.GET.get('location_id')
    if location_id:
        sublocations = SubLocation.objects.filter(location_id=location_id).values('id', 'name')
        return JsonResponse(list(sublocations), safe=False)
    return JsonResponse([], safe=False)
