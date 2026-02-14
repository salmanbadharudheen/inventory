from django.urls import path
from .views import (
    AssetListView, AssetCreateView, AssetDetailView, AssetUpdateView, AssetImportView, 
    download_sample_csv, get_subcategories, get_departments, get_buildings, get_floors, get_rooms, lookup_asset,
    CategoryListView, CategoryCreateView, CategoryUpdateView,
    SubCategoryListView, SubCategoryCreateView, SubCategoryUpdateView,
    VendorListView, VendorCreateView, VendorUpdateView,
    GroupListView, GroupCreateView, GroupUpdateView,
    SubGroupListView, SubGroupCreateView, SubGroupUpdateView, get_subgroups,
    BrandListView, BrandCreateView, BrandUpdateView,
    CompanyListView, CompanyCreateView, CompanyUpdateView,
    SupplierListView, SupplierCreateView, SupplierUpdateView,
    CustodianListView, CustodianCreateView, CustodianUpdateView,
    AssetRemarksListView, AssetRemarksCreateView, AssetRemarksUpdateView
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
    path('ajax/lookup/', lookup_asset, name='asset-lookup'),
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

    # Configuration: Groups
    path('groups/', GroupListView.as_view(), name='group-list'),
    path('groups/add/', GroupCreateView.as_view(), name='group-create'),
    path('groups/<int:pk>/edit/', GroupUpdateView.as_view(), name='group-edit'),

    # Configuration: SubGroups
    path('subgroups/', SubGroupListView.as_view(), name='subgroup-list'),
    path('subgroups/add/', SubGroupCreateView.as_view(), name='subgroup-create'),
    path('subgroups/<int:pk>/edit/', SubGroupUpdateView.as_view(), name='subgroup-edit'),
    path('ajax/subgroups/', get_subgroups, name='get-subgroups'),

    # Configuration: Brands
    path('brands/', BrandListView.as_view(), name='brand-list'),
    path('brands/add/', BrandCreateView.as_view(), name='brand-create'),
    path('brands/<int:pk>/edit/', BrandUpdateView.as_view(), name='brand-edit'),

    # Configuration: Companies
    path('companies/', CompanyListView.as_view(), name='company-list'),
    path('companies/add/', CompanyCreateView.as_view(), name='company-create'),
    path('companies/<int:pk>/edit/', CompanyUpdateView.as_view(), name='company-edit'),

    # Configuration: Suppliers
    path('suppliers/', SupplierListView.as_view(), name='supplier-list'),
    path('suppliers/add/', SupplierCreateView.as_view(), name='supplier-create'),
    path('suppliers/<int:pk>/edit/', SupplierUpdateView.as_view(), name='supplier-edit'),

    # Configuration: Custodians
    path('custodians/', CustodianListView.as_view(), name='custodian-list'),
    path('custodians/add/', CustodianCreateView.as_view(), name='custodian-create'),
    path('custodians/<int:pk>/edit/', CustodianUpdateView.as_view(), name='custodian-edit'),

    # Configuration: Asset Remarks
    path('remarks/', AssetRemarksListView.as_view(), name='assetremarks-list'),
    path('remarks/add/', AssetRemarksCreateView.as_view(), name='assetremarks-create'),
    path('remarks/<int:pk>/edit/', AssetRemarksUpdateView.as_view(), name='assetremarks-edit'),
]
