from django.contrib import admin
from .models import (
    Asset, Category, SubCategory, Vendor, Group, SubGroup, 
    Brand, Company, Supplier, Custodian, AssetRemarks,
    AssetAttachment, AssetActivityLog, ApprovalRequest, ApprovalLog, AssetTransfer
)

@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['asset_tag', 'name', 'category', 'status', 'department', 'organization']
    list_filter = ['status', 'category', 'organization', 'created_at']
    search_fields = ['asset_tag', 'name', 'custom_asset_tag']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'useful_life_years', 'organization']
    list_filter = ['organization', 'created_at']
    search_fields = ['name', 'code']

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'organization']
    list_filter = ['category', 'organization']
    search_fields = ['name']

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'organization']
    list_filter = ['organization', 'created_at']
    search_fields = ['name', 'email']

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization']
    list_filter = ['organization']
    search_fields = ['name', 'code']

@admin.register(SubGroup)
class SubGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'group', 'code', 'organization']
    list_filter = ['group', 'organization']
    search_fields = ['name', 'code']

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'organization']
    list_filter = ['organization']
    search_fields = ['name', 'code']

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'contact_person', 'organization']
    list_filter = ['organization']
    search_fields = ['name', 'code']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'contact_person', 'organization']
    list_filter = ['organization']
    search_fields = ['name', 'code']

@admin.register(Custodian)
class CustodianAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'user', 'department_name', 'organization']
    list_filter = ['organization']
    search_fields = ['employee_id', 'user__username']

@admin.register(AssetRemarks)
class AssetRemarksAdmin(admin.ModelAdmin):
    list_display = ['remark', 'organization']
    list_filter = ['organization']
    search_fields = ['remark']

@admin.register(AssetAttachment)
class AssetAttachmentAdmin(admin.ModelAdmin):
    list_display = ['asset', 'attachment_type', 'created_at']
    list_filter = ['attachment_type', 'created_at']
    search_fields = ['asset__asset_tag']

@admin.register(AssetActivityLog)
class AssetActivityLogAdmin(admin.ModelAdmin):
    list_display = ['asset', 'action_type', 'actor', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['asset__asset_tag']
    readonly_fields = ['created_at']

@admin.register(ApprovalRequest)
class ApprovalRequestAdmin(admin.ModelAdmin):
    list_display = ['request_type', 'status', 'requester', 'asset', 'created_at']
    list_filter = ['request_type', 'status', 'created_at', 'organization']
    search_fields = ['asset__asset_tag', 'requester__username']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Request Info', {
            'fields': ('id', 'request_type', 'status', 'requester', 'asset')
        }),
        ('Details', {
            'fields': ('data', 'comments')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ApprovalLog)
class ApprovalLogAdmin(admin.ModelAdmin):
    list_display = ['approval_request', 'approver', 'decision', 'approval_level', 'created_at']
    list_filter = ['decision', 'approval_level', 'created_at']
    search_fields = ['approver__username', 'approval_request__asset__asset_tag']
    readonly_fields = ['id', 'created_at']
@admin.register(AssetTransfer)
class AssetTransferAdmin(admin.ModelAdmin):
    list_display = ['asset', 'transfer_date', 'status', 'transferred_to_user', 'transferred_to_department', 'organization']
    list_filter = ['status', 'transfer_date', 'organization', 'created_at']
    search_fields = ['asset__asset_tag', 'asset__name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        ('Transfer Info', {
            'fields': ('id', 'asset', 'transfer_date', 'status')
        }),
        ('From', {
            'fields': ('transferred_from_user', 'transferred_from_department', 'transferred_from_location')
        }),
        ('To', {
            'fields': ('transferred_to_user', 'transferred_to_department', 'transferred_to_location')
        }),
        ('Details', {
            'fields': ('expected_receipt_date', 'actual_receipt_date', 'transfer_reason', 'notes', 'received_comments')
        }),
        ('Tracking', {
            'fields': ('created_by', 'received_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )