from django.urls import path
from .views import (
    AdminCreateView, UserListView, 
    AdminDashboardView, AdminUserListView, AdminOrgListView, AdminUserDetailView,
    OrgAssetTagSettingsView, OrgTagPreviewAPI,
    AdminOrgCreateView, AdminOrgUpdateView, AdminOrgDeleteView, AdminOrgAssignAdminView, AdminOrgDashboardView,
    AdminOrgToggleStatusView,
    OwnerLoginView, OwnerLogoutView, AdminOrgLoginView, OwnerExitOrgModeView,
)

urlpatterns = [
    path('add/', AdminCreateView.as_view(), name='user-add'),
    path('', UserListView.as_view(), name='user-list'),
    # Owner login / logout (separate from regular user login)
    path('owner/login/', OwnerLoginView.as_view(), name='owner-login'),
    path('owner/logout/', OwnerLogoutView.as_view(), name='owner-logout'),
    path('owner/exit-org-mode/', OwnerExitOrgModeView.as_view(), name='owner-exit-org-mode'),
    # Admin panel routes
    path('admin/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/users/<int:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/organizations/', AdminOrgListView.as_view(), name='admin-orgs'),
    path('admin/organizations/<uuid:pk>/dashboard/', AdminOrgDashboardView.as_view(), name='admin-org-dashboard'),
    path('admin/organizations/<uuid:pk>/login/', AdminOrgLoginView.as_view(), name='admin-org-login'),
    path('admin/organizations/create/', AdminOrgCreateView.as_view(), name='admin-org-create'),
    path('admin/organizations/<uuid:pk>/edit/', AdminOrgUpdateView.as_view(), name='admin-org-edit'),
    path('admin/organizations/<uuid:pk>/delete/', AdminOrgDeleteView.as_view(), name='admin-org-delete'),
    path('admin/organizations/<uuid:pk>/toggle-status/', AdminOrgToggleStatusView.as_view(), name='admin-org-toggle-status'),
    path('admin/organizations/<uuid:pk>/assign-admin/', AdminOrgAssignAdminView.as_view(), name='admin-org-assign-admin'),
    path('admin/organizations/<uuid:pk>/tag-settings/', OrgAssetTagSettingsView.as_view(), name='org-tag-settings'),
    path('admin/organizations/<uuid:pk>/tag-preview/', OrgTagPreviewAPI.as_view(), name='org-tag-preview'),
]
