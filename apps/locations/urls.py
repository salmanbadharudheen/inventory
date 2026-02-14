from django.urls import path
from .views import (
    BranchListView, BranchCreateView, BranchUpdateView,
    DepartmentListView, DepartmentCreateView, DepartmentUpdateView,
    BuildingListView, BuildingCreateView,
    FloorListView, FloorCreateView,
    RoomListView, RoomCreateView,
    RegionListView, RegionCreateView, RegionUpdateView,
    SiteListView, SiteCreateView, SiteUpdateView, get_sites,
    LocationListView, LocationCreateView, LocationUpdateView, get_locations,
    SubLocationListView, SubLocationCreateView, SubLocationUpdateView, get_sublocations
)

urlpatterns = [
    # Branches
    path('branches/', BranchListView.as_view(), name='branch-list'),
    path('branches/add/', BranchCreateView.as_view(), name='branch-create'),
    path('branches/<int:pk>/edit/', BranchUpdateView.as_view(), name='branch-edit'),

    # Departments
    path('departments/', DepartmentListView.as_view(), name='department-list'),
    path('departments/add/', DepartmentCreateView.as_view(), name='department-create'),
    path('departments/<int:pk>/edit/', DepartmentUpdateView.as_view(), name='department-edit'),

    # Buildings
    path('buildings/', BuildingListView.as_view(), name='building-list'),
    path('buildings/add/', BuildingCreateView.as_view(), name='building-create'),

    # Floors
    path('floors/', FloorListView.as_view(), name='floor-list'),
    path('floors/add/', FloorCreateView.as_view(), name='floor-create'),

    # Rooms
    path('rooms/', RoomListView.as_view(), name='room-list'),
    path('rooms/add/', RoomCreateView.as_view(), name='room-create'),

    # Regions
    path('regions/', RegionListView.as_view(), name='region-list'),
    path('regions/add/', RegionCreateView.as_view(), name='region-create'),
    path('regions/<int:pk>/edit/', RegionUpdateView.as_view(), name='region-edit'),

    # Sites
    path('sites/', SiteListView.as_view(), name='site-list'),
    path('sites/add/', SiteCreateView.as_view(), name='site-create'),
    path('sites/<int:pk>/edit/', SiteUpdateView.as_view(), name='site-edit'),
    path('ajax/sites/', get_sites, name='get-sites'),

    # Locations
    path('locations_list/', LocationListView.as_view(), name='location-list'), # Using locations_list to avoid conflict with app name
    path('locations_list/add/', LocationCreateView.as_view(), name='location-create'),
    path('locations_list/<int:pk>/edit/', LocationUpdateView.as_view(), name='location-edit'),
    path('ajax/locations/', get_locations, name='get-locations'),

    # SubLocations
    path('sublocations/', SubLocationListView.as_view(), name='sublocation-list'),
    path('sublocations/add/', SubLocationCreateView.as_view(), name='sublocation-create'),
    path('sublocations/<int:pk>/edit/', SubLocationUpdateView.as_view(), name='sublocation-edit'),
    path('ajax/sublocations/', get_sublocations, name='get-sublocations'),
]
