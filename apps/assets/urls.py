from django.urls import path
from .views import (
    AssetListView, AssetCreateView, AssetDetailView, AssetUpdateView, AssetImportView, 
    download_sample_csv, get_subcategories, get_departments, get_buildings, get_floors, get_rooms,
    CategoryListView, CategoryCreateView, CategoryUpdateView,
    SubCategoryListView, SubCategoryCreateView, SubCategoryUpdateView,
    VendorListView, VendorCreateView, VendorUpdateView
)

urlpatterns = [
    # Assets
    path('', AssetListView.as_view(), name='asset-list'),
    path('import/', AssetImportView.as_view(), name='asset-import'),
    path('import/sample/', download_sample_csv, name='asset-import-sample'),
    path('ajax/subcategories/', get_subcategories, name='get-subcategories'),
    path('ajax/departments/', get_departments, name='get-departments'),
    path('ajax/buildings/', get_buildings, name='get-buildings'),
    path('ajax/floors/', get_floors, name='get-floors'),
    path('ajax/rooms/', get_rooms, name='get-rooms'),
    path('add/', AssetCreateView.as_view(), name='asset-create'),
    path('<uuid:pk>/', AssetDetailView.as_view(), name='asset-detail'),
    path('<uuid:pk>/edit/', AssetUpdateView.as_view(), name='asset-update'),

    # Configuration: Categories
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('categories/add/', CategoryCreateView.as_view(), name='category-create'),
    path('categories/<int:pk>/edit/', CategoryUpdateView.as_view(), name='category-edit'),

    # Configuration: SubCategories
    path('subcategories/', SubCategoryListView.as_view(), name='subcategory-list'),
    path('subcategories/add/', SubCategoryCreateView.as_view(), name='subcategory-create'),
    path('subcategories/<int:pk>/edit/', SubCategoryUpdateView.as_view(), name='subcategory-edit'),
    
    # Configuration: Vendors
    path('vendors/', VendorListView.as_view(), name='vendor-list'),
    path('vendors/add/', VendorCreateView.as_view(), name='vendor-create'),
    path('vendors/<int:pk>/edit/', VendorUpdateView.as_view(), name='vendor-edit'),
]
