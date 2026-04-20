from django.urls import path
from .views import (
    AdminCreateView, UserListView, 
    AdminDashboardView, AdminUserListView, AdminOrgListView, AdminUserDetailView,
    OrgAssetTagSettingsView, OrgTagPreviewAPI,
)

urlpatterns = [
    path('add/', AdminCreateView.as_view(), name='user-add'),
    path('', UserListView.as_view(), name='user-list'),
    # Admin panel routes
    path('admin/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/organizations/', AdminOrgListView.as_view(), name='admin-orgs'),
    path('admin/organizations/<uuid:pk>/tag-settings/', OrgAssetTagSettingsView.as_view(), name='org-tag-settings'),
    path('admin/organizations/<uuid:pk>/tag-preview/', OrgTagPreviewAPI.as_view(), name='org-tag-preview'),
]
