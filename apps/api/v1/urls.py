from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'api_v1'

urlpatterns = [
    # Root
    path('', views.api_root, name='api-root'),
    
    # Authentication endpoints
    path('auth/login/', views.LoginAPIView.as_view(), name='login'),
    path('auth/logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('auth/register/', views.RegisterAPIView.as_view(), name='register'),
    path('auth/profile/', views.UserProfileAPIView.as_view(), name='profile'),
    path('auth/change-password/', views.ChangePasswordAPIView.as_view(), name='change-password'),
    
    # JWT Token endpoints
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Dashboard
    path('dashboard/', views.DashboardAPIView.as_view(), name='dashboard'),

    # Assets
    path('assets/', views.AssetListAPIView.as_view(), name='asset-list'),
    path('assets/create/', views.AssetCreateAPIView.as_view(), name='asset-create'),
    path('assets/lookup/', views.AssetLookupByTagAPIView.as_view(), name='asset-lookup-by-tag'),
    path('assets/<uuid:pk>/', views.AssetDetailAPIView.as_view(), name='asset-detail'),

    # Asset Transfer PDF Export
    path('assets/export/pdf/', views.AssetTransferExportPDFView.as_view(), name='asset-transfer-export-pdf'),

    # Lookups (for dropdown pickers on mobile)
    path('lookups/categories/', views.CategoryListAPIView.as_view(), name='lookup-categories'),
    path('lookups/sub-categories/', views.SubCategoryListAPIView.as_view(), name='lookup-sub-categories'),
    path('lookups/groups/', views.GroupListAPIView.as_view(), name='lookup-groups'),
    path('lookups/sub-groups/', views.SubGroupListAPIView.as_view(), name='lookup-sub-groups'),
    path('lookups/companies/', views.CompanyListAPIView.as_view(), name='lookup-companies'),
    path('lookups/regions/', views.RegionListAPIView.as_view(), name='lookup-regions'),
    path('lookups/sites/', views.SiteListAPIView.as_view(), name='lookup-sites'),
    path('lookups/buildings/', views.BuildingListAPIView.as_view(), name='lookup-buildings'),
    path('lookups/floors/', views.FloorListAPIView.as_view(), name='lookup-floors'),
    path('lookups/branches/', views.BranchListAPIView.as_view(), name='lookup-branches'),
    path('lookups/departments/', views.DepartmentListAPIView.as_view(), name='lookup-departments'),
]
