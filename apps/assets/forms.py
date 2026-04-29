import os

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from .models import (Asset, AssetAttachment, Vendor, Category, SubCategory,
                     Group, SubGroup, Brand, Company, Supplier, Custodian, AssetRemarks, AssetTransfer, AssetDisposal)
from apps.locations.models import Branch, Department, Building, Floor, Room, Region, Site, Location, SubLocation
from django.utils.translation import gettext_lazy as _


MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024   # 5 MB
MAX_DOCUMENT_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
ALLOWED_DOCUMENT_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.jpg', '.jpeg', '.png', '.webp'
}

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        exclude = ['organization', 'created_by', 'is_deleted', 'custom_fields', 'asset_tag', 'salvage_value', 'useful_life_years']
        widgets = {
            'purchase_date': forms.DateInput(attrs={'type': 'date'}),
            'warranty_start': forms.DateInput(attrs={'type': 'date'}),
            'warranty_end': forms.DateInput(attrs={'type': 'date'}),
            'next_maintenance_date': forms.DateInput(attrs={'type': 'date'}),
            'po_date': forms.DateInput(attrs={'type': 'date'}),
            'do_date': forms.DateInput(attrs={'type': 'date'}),
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'date_placed_in_service': forms.DateInput(attrs={'type': 'date'}),
            'tagged_date': forms.DateInput(attrs={'type': 'date'}),
            'insurance_start_date': forms.DateInput(attrs={'type': 'date'}),
            'insurance_end_date': forms.DateInput(attrs={'type': 'date'}),
            'maintenance_start_date': forms.DateInput(attrs={'type': 'date'}),
            'maintenance_end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'useful_life_years': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'quantity': forms.NumberInput(attrs={'min': '1', 'value': '1'}),
            'asset_code': forms.TextInput(attrs={'placeholder': 'e.g. CODE-456'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'short_description': forms.TextInput(attrs={'placeholder': 'Brief summary'}),
            'erp_asset_number': forms.TextInput(attrs={'placeholder': 'ERP Reference'}),
            'parent': forms.HiddenInput(), # Hidden, populated by JS lookup
        }

    def __init__(self, *args, **kwargs):
        try:
            self.request = kwargs.pop('request', None)
            super().__init__(*args, **kwargs)
            
            # Style all fields
            for field_name, field in self.fields.items():
                field.widget.attrs['class'] = 'form-control'
                if field.required:
                    field.widget.attrs['class'] += ' required'
            
            # Filter dropdowns by Organization if user is logged in
            if self.request and self.request.user.is_authenticated and hasattr(self.request.user, 'organization') and self.request.user.organization:
                org = self.request.user.organization
                User = get_user_model()
                self.fields['category'].queryset = Category.objects.filter(organization=org)
                self.fields['sub_category'].queryset = SubCategory.objects.filter(category__organization=org)
                self.fields['branch'].queryset = Branch.objects.filter(organization=org)
                self.fields['department'].queryset = Department.objects.filter(branch__organization=org)
                self.fields['building'].queryset = Building.objects.filter(branch__organization=org)
                self.fields['floor'].queryset = Floor.objects.filter(building__branch__organization=org)
                self.fields['room'].queryset = Room.objects.filter(floor__building__branch__organization=org)
                self.fields['vendor'].queryset = Vendor.objects.filter(organization=org)
                
                # New Fields Organization Filtering
                self.fields['group'].queryset = Group.objects.filter(organization=org)
                self.fields['sub_group'].queryset = SubGroup.objects.filter(group__organization=org)
                self.fields['brand_new'].queryset = Brand.objects.filter(organization=org)
                self.fields['company'].queryset = Company.objects.filter(organization=org)
                self.fields['supplier'].queryset = Supplier.objects.filter(organization=org)
                self.fields['custodian'].queryset = Custodian.objects.filter(organization=org)
                self.fields['assigned_to'].queryset = User.objects.filter(organization=org)
                self.fields['region'].queryset = Region.objects.filter(organization=org)
                self.fields['site'].queryset = Site.objects.filter(region__organization=org)
                self.fields['location'].queryset = Location.objects.filter(site__region__organization=org)
                self.fields['sub_location'].queryset = SubLocation.objects.filter(location__site__region__organization=org)
                self.fields['asset_remarks'].queryset = AssetRemarks.objects.filter(organization=org)
                
                # Optimized Parent field for AJAX - prevent loading all assets
                if 'parent' in self.fields:
                    self.fields['parent'].queryset = Asset.objects.none()

                    if 'parent' in self.data:
                        try:
                            parent_id = self.data.get('parent')
                            if parent_id:
                                self.fields['parent'].queryset = Asset.objects.filter(id=parent_id, organization=org)
                        except (ValueError, TypeError):
                            pass  # invalid input from the client; ignore and fallback to empty queryset
                    elif self.instance.pk and self.instance.parent:
                        self.fields['parent'].queryset = Asset.objects.filter(pk=self.instance.parent.pk, organization=org)
        except Exception:
            import traceback
            print("ERROR in AssetForm.__init__:")
            print(traceback.format_exc())
            raise

    def clean(self):
        cleaned_data = super().clean()

        # Validate asset_code uniqueness per organization
        asset_code = cleaned_data.get('asset_code')
        if asset_code:
            qs = Asset.objects.filter(
                organization=self.request.user.organization,
                asset_code=asset_code,
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError({'asset_code': _('An asset with this Asset Code already exists.')})

        field_rules = {
            'image': (ALLOWED_IMAGE_EXTENSIONS, MAX_IMAGE_UPLOAD_BYTES),
            'po_file': (ALLOWED_DOCUMENT_EXTENSIONS, MAX_DOCUMENT_UPLOAD_BYTES),
            'invoice_file': (ALLOWED_DOCUMENT_EXTENSIONS, MAX_DOCUMENT_UPLOAD_BYTES),
            'delivery_note_file': (ALLOWED_DOCUMENT_EXTENSIONS, MAX_DOCUMENT_UPLOAD_BYTES),
            'insurance_file': (ALLOWED_DOCUMENT_EXTENSIONS, MAX_DOCUMENT_UPLOAD_BYTES),
            'amc_file': (ALLOWED_DOCUMENT_EXTENSIONS, MAX_DOCUMENT_UPLOAD_BYTES),
        }

        for field_name, (allowed_extensions, max_bytes) in field_rules.items():
            upload = cleaned_data.get(field_name)
            if not upload:
                continue

            extension = os.path.splitext(upload.name)[1].lower()
            if extension not in allowed_extensions:
                raise ValidationError({
                    field_name: _(
                        f"Unsupported file type for {field_name.replace('_', ' ')}. "
                        f"Allowed: {', '.join(sorted(allowed_extensions))}"
                    )
                })

            if upload.size > max_bytes:
                max_mb = max_bytes // (1024 * 1024)
                raise ValidationError({
                    field_name: _(
                        f"{field_name.replace('_', ' ').title()} is too large. Maximum allowed size is {max_mb} MB."
                    )
                })

        return cleaned_data

class AssetAttachmentForm(forms.ModelForm):
    class Meta:
        model = AssetAttachment
        fields = ['file', 'attachment_type', 'description']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'useful_life_years', 'depreciation_method', 'default_salvage_value', 'default_expected_units']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Electronics'}),
            'useful_life_years': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'depreciation_method': forms.Select(attrs={'class': 'form-control'}),
            'default_salvage_value': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'default_expected_units': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ['category', 'name']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Laptops'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and self.request.user.organization:
            self.fields['category'].queryset = Category.objects.filter(organization=self.request.user.organization)

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = ['name', 'contact_person', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Tech Supplies Inc.'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AssetImportForm(forms.Form):
    import_file = forms.FileField(
        label="Select File",
        help_text="Upload .csv or .xlsx file. Headers must match the template."
    )

    def clean_import_file(self):
        import_file = self.cleaned_data['import_file']
        name = import_file.name.lower()
        if not (name.endswith('.csv') or name.endswith('.xlsx')):
            raise forms.ValidationError("Only .csv and .xlsx files are allowed.")
        return import_file

# New Master Data Forms

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., IT Equipment'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class SubGroupForm(forms.ModelForm):
    class Meta:
        model = SubGroup
        fields = ['group', 'name', 'code', 'description']
        widgets = {
            'group': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Computers'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and hasattr(self.request.user, 'organization') and self.request.user.organization:
            self.fields['group'].queryset = Group.objects.filter(organization=self.request.user.organization)

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Dell'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['name', 'code', 'address', 'contact_person', 'email', 'phone']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., ABC Corp'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'code', 'contact_person', 'email', 'phone', 'address']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Tech Supplies Ltd'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CustodianForm(forms.ModelForm):
    class Meta:
        model = Custodian
        fields = ['user', 'employee_id', 'department_name', 'phone']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., EMP001'}),
            'department_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and hasattr(self.request.user, 'organization') and self.request.user.organization:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.fields['user'].queryset = User.objects.filter(organization=self.request.user.organization)

class AssetRemarksForm(forms.ModelForm):
    class Meta:
        model = AssetRemarks
        fields = ['remark', 'description']
        widgets = {
            'remark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Needs Repair'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AssetTransferForm(forms.ModelForm):
    """Form for creating and updating asset transfers"""
    
    
    class Meta:
        model = AssetTransfer
        fields = [
            'transfer_no',
            'transfer_description',
            'transferred_to_region',
            'transferred_to_site',
            'transferred_to_building',
            'transferred_to_floor',
            'transferred_to_room',
            'transferred_to_company',
            'transferred_to_department',
            'transferred_to_custodian',
            'movement_reason',
            'requester_name',
            'asset',
        ]
        widgets = {
            'transfer_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional transfer reference'}),
            'transfer_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Short description for this transfer'}),
            'transferred_to_region': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_site': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_building': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_floor': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_room': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_company': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_department': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_custodian': forms.Select(attrs={'class': 'form-control'}),
            'movement_reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Specific reason for this movement'
            }),
            'requester_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Requester name (free text)'}),
            'asset': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Filter by organization
        if self.request and hasattr(self.request.user, 'organization') and self.request.user.organization:
            org = self.request.user.organization
            self.fields['asset'].queryset = Asset.objects.filter(organization=org)
            # Populate the 'to' selects
            self.fields['transferred_to_region'].queryset = Region.objects.filter(organization=org)
            self.fields['transferred_to_site'].queryset = Site.objects.filter(region__organization=org)
            # Buildings are linked to Locations -> derive buildings available via locations
            self.fields['transferred_to_building'].queryset = Building.objects.filter(locations__site__region__organization=org).distinct()
            self.fields['transferred_to_floor'].queryset = Floor.objects.filter(building__branch__organization=org)
            self.fields['transferred_to_room'].queryset = Room.objects.filter(floor__building__branch__organization=org)
            self.fields['transferred_to_company'].queryset = Company.objects.filter(organization=org)
            self.fields['transferred_to_department'].queryset = Department.objects.filter(branch__organization=org)
            self.fields['transferred_to_custodian'].queryset = Custodian.objects.filter(organization=org)
        
        # Make all fields optional (bulk form handles multiple assets via JS)
        self.fields['transfer_no'].required = False
        self.fields['asset'].required = False
        self.fields['transfer_description'].required = False
        self.fields['transferred_to_region'].required = False
        self.fields['transferred_to_site'].required = False
        self.fields['transferred_to_building'].required = False
        self.fields['transferred_to_floor'].required = False
        self.fields['transferred_to_room'].required = False
        self.fields['transferred_to_company'].required = False
        self.fields['transferred_to_department'].required = False
        self.fields['transferred_to_custodian'].required = False
        self.fields['movement_reason'].required = False
        self.fields['requester_name'].required = False


class AssetTransferReceiveForm(forms.ModelForm):
    """Form for receiving/confirming asset transfer"""
    
    class Meta:
        model = AssetTransfer
        fields = ['actual_receipt_date', 'received_comments', 'status']
        widgets = {
            'actual_receipt_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'received_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Receiver confirmation notes'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow valid status transitions
        self.fields['status'].choices = [
            (AssetTransfer.Status.RECEIVED, _('Received')),
            (AssetTransfer.Status.REJECTED, _('Rejected')),
        ]
        self.fields['actual_receipt_date'].required = False
        self.fields['received_comments'].required = False


class AssetDisposalForm(forms.ModelForm):
    """Form for creating/editing asset disposal requests with searchable asset field"""
    
    # Searchable asset field using ModelChoiceField with custom widget
    asset = forms.ModelChoiceField(
        queryset=Asset.objects.all(),
        widget=forms.Select(attrs={
            'class': 'form-control searchable-select',
            'required': True,
            'data-placeholder': 'Search and select an asset...'
        })
    )
    
    class Meta:
        model = AssetDisposal
        fields = ['asset', 'disposal_method', 'reason', 'disposal_date', 'estimated_salvage_value', 'notes']
        widgets = {
            'disposal_method': forms.Select(attrs={'class': 'form-control'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for disposal'}),
            'disposal_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'estimated_salvage_value': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0.00', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Additional notes'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Filter assets by organization - supports searching by asset_tag and name
        if self.request and self.request.user.is_authenticated and hasattr(self.request.user, 'organization') and self.request.user.organization:
            org = self.request.user.organization
            self.fields['asset'].queryset = Asset.objects.filter(
                organization=org,
                status__in=[Asset.Status.ACTIVE, Asset.Status.IN_STORAGE, Asset.Status.UNDER_MAINTENANCE]
            ).order_by('asset_tag')
        
        self.fields['disposal_date'].required = False
        self.fields['estimated_salvage_value'].required = False
        self.fields['reason'].required = False
        self.fields['notes'].required = False
    
    def __str__(self):
        """Display asset with tag and name for better searchability"""
        return f"{self.asset_tag} - {self.name}"


class AssetDisposalManagerApprovalForm(forms.ModelForm):
    """Form for manager approval of asset disposal requests (step 1)"""
    
    class Meta:
        model = AssetDisposal
        fields = ['status', 'manager_rejection_reason', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'manager_rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for rejection'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Manager comments'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow manager to approve or reject
        self.fields['status'].choices = [
            (AssetDisposal.Status.MANAGER_APPROVED, _('Approve & Send to Admin')),
            (AssetDisposal.Status.REJECTED, _('Reject')),
        ]


class AssetDisposalApprovalForm(forms.ModelForm):
    """Form for admin final approval/rejection of asset disposal requests (step 2)"""
    
    class Meta:
        model = AssetDisposal
        fields = ['status', 'rejection_reason', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'rejection_reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Reason for rejection'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Admin approval notes'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only allow admin to approve or reject
        self.fields['status'].choices = [
            (AssetDisposal.Status.APPROVED, _('Approve')),
            (AssetDisposal.Status.REJECTED, _('Reject')),
        ]
        self.fields['rejection_reason'].required = False
        self.fields['notes'].required = False