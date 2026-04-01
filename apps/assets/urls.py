from django.urls import path
from .views import (
    AssetListView, AssetCreateView, AssetDetailView, AssetUpdateView, AssetImportView, 
    BulkAssetActionView, ExportAssetExcelView, DepreciationReportCategoryView, DepreciationReportGroupView, DepreciationReportLocationView, DepreciationReportDepartmentView,
    download_sample_csv, download_sample_excel, get_subcategories, get_departments, get_buildings, get_buildings_by_site, get_floors, get_rooms, get_locations, lookup_asset,
    ajax_create_category, ajax_create_subcategory,
    generate_asset_codes, download_asset_barcode, download_asset_qr, download_asset_label, download_barcode_batch,
    CategoryListView, CategoryCreateView, CategoryUpdateView,
    SubCategoryListView, SubCategoryCreateView, SubCategoryUpdateView,
    VendorListView, VendorCreateView, VendorUpdateView,
    GroupListView, GroupCreateView, GroupUpdateView,
    SubGroupListView, SubGroupCreateView, SubGroupUpdateView, get_subgroups,
    BrandListView, BrandCreateView, BrandUpdateView,
    CompanyListView, CompanyCreateView, CompanyUpdateView,
    SupplierListView, SupplierCreateView, SupplierUpdateView,
    CustodianListView, CustodianCreateView, CustodianUpdateView,
    AssetRemarksListView, AssetRemarksCreateView, AssetRemarksUpdateView,
    ApprovalListView, ApprovalDetailView, ApprovalApproveView, CreateApprovalRequestView,
    AssetTransferListView, AssetTransferCreateView, AssetTransferDetailView, AssetTransferUpdateView, AssetTransferReceiveView, AssetTransferExportExcelView,
    AssetDisposalListView, AssetDisposalCreateView, AssetDisposalDetailView, AssetDisposalManagerApproveView, AssetDisposalApproveView,
    ReportsListView, MastersListView, MastersExportExcelView
)
from .views_approval import (
    AssetApprovalRequestCreateView,
    ApprovalRequestListView,
    ApprovalRequestDetailView,
    ApprovalRequestApproveView,
    ApprovalRequestRejectView,
    ApprovalPendingListView,
)

urlpatterns = [
    # Reports
    path('reports/', ReportsListView.as_view(), name='reports-list'),
    path('depreciation/category/', DepreciationReportCategoryView.as_view(), name='depreciation-category'),
    path('depreciation/group/', DepreciationReportGroupView.as_view(), name='depreciation-group'),
    path('depreciation/location/', DepreciationReportLocationView.as_view(), name='depreciation-location'),
    path('depreciation/department/', DepreciationReportDepartmentView.as_view(), name='depreciation-department'),
    
    # Masters
    path('masters/', MastersListView.as_view(), name='masters-list'),
    path('masters/export/excel/', MastersExportExcelView.as_view(), name='masters-export-excel'),
    
    # Assets
    path('', AssetListView.as_view(), name='asset-list'),
    path('bulk-action/', BulkAssetActionView.as_view(), name='asset-bulk-action'),
    path('export/excel/', ExportAssetExcelView.as_view(), name='asset-export-excel'),
    path('import/', AssetImportView.as_view(), name='asset-import'),
    path('import/sample/csv/', download_sample_csv, name='asset-import-sample'),
    path('import/sample/excel/', download_sample_excel, name='asset-import-sample-excel'),
    path('ajax/subcategories/', get_subcategories, name='get-subcategories'),
    path('ajax/category/create/', ajax_create_category, name='ajax-create-category'),
    path('ajax/subcategory/create/', ajax_create_subcategory, name='ajax-create-subcategory'),
    path('ajax/departments/', get_departments, name='get-departments'),
    path('ajax/buildings/', get_buildings, name='get-buildings'),
    path('ajax/buildings_by_site/', get_buildings_by_site, name='get-buildings-by-site'),
    path('ajax/floors/', get_floors, name='get-floors'),
    path('ajax/rooms/', get_rooms, name='get-rooms'),
    path('ajax/locations/', get_locations, name='get-locations'),
    path('ajax/lookup/', lookup_asset, name='asset-lookup'),
    path('add/', AssetCreateView.as_view(), name='asset-create'),
    path('<uuid:pk>/', AssetDetailView.as_view(), name='asset-detail'),
    path('<uuid:pk>/edit/', AssetUpdateView.as_view(), name='asset-update'),
    
    # Barcode & QR Code endpoints
    path('<uuid:pk>/codes/generate/', generate_asset_codes, name='generate-asset-codes'),
    path('<uuid:pk>/barcode/download/', download_asset_barcode, name='download-asset-barcode'),
    path('<uuid:pk>/qr/download/', download_asset_qr, name='download-asset-qr'),
    path('<uuid:pk>/label/download/', download_asset_label, name='download-asset-label'),
    path('barcodes/download/batch/', download_barcode_batch, name='download-barcode-batch'),

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
    
    # Approval Workflow
    path('approvals/', ApprovalListView.as_view(), name='approval_list'),
    path('approvals/<uuid:pk>/', ApprovalDetailView.as_view(), name='approval_detail'),
    path('approvals/<uuid:pk>/approve/', ApprovalApproveView.as_view(), name='approval_approve'),
    path('approvals/new/', CreateApprovalRequestView.as_view(), name='approval_create'),
    
    # Asset Approval Request (New Feature)
    path('approval-requests/', ApprovalRequestListView.as_view(), name='approval-request-list'),
    path('approval-requests/new/', AssetApprovalRequestCreateView.as_view(), name='approval-request-create'),
    path('approval-requests/<uuid:pk>/', ApprovalRequestDetailView.as_view(), name='approval-request-detail'),
    path('approval-requests/<uuid:pk>/approve/', ApprovalRequestApproveView.as_view(), name='approval-request-approve'),
    path('approval-requests/<uuid:pk>/reject/', ApprovalRequestRejectView.as_view(), name='approval-request-reject'),
    path('approval-requests/pending/', ApprovalPendingListView.as_view(), name='approval-pending-list'),
    
    # Asset Transfer Workflow
    path('transfers/', AssetTransferListView.as_view(), name='transfer-list'),
    path('transfers/export/excel/', AssetTransferExportExcelView.as_view(), name='transfer-export-excel'),
    path('transfers/add/', AssetTransferCreateView.as_view(), name='transfer-create'),
    path('transfers/<uuid:pk>/', AssetTransferDetailView.as_view(), name='transfer-detail'),
    path('transfers/<uuid:pk>/edit/', AssetTransferUpdateView.as_view(), name='transfer-update'),
    path('transfers/<uuid:pk>/receive/', AssetTransferReceiveView.as_view(), name='transfer-receive'),
    
    # Asset Disposal Workflow (Two-step approval: Manager → Admin)
    path('disposals/', AssetDisposalListView.as_view(), name='disposal-list'),
    path('disposals/add/', AssetDisposalCreateView.as_view(), name='disposal-create'),
    path('disposals/<uuid:pk>/', AssetDisposalDetailView.as_view(), name='disposal-detail'),
    path('disposals/<uuid:pk>/manager-approve/', AssetDisposalManagerApproveView.as_view(), name='disposal-manager-approve'),
    path('disposals/<uuid:pk>/approve/', AssetDisposalApproveView.as_view(), name='disposal-approve'),
]