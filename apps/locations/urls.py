from django.urls import path
from .views import (
    BranchListView, BranchCreateView, BranchUpdateView,
    DepartmentListView, DepartmentCreateView, DepartmentUpdateView,
    BuildingListView, BuildingCreateView,
    FloorListView, FloorCreateView,
    RoomListView, RoomCreateView
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
]
