from django import forms
from .models import (Asset, AssetAttachment, Vendor, Category, SubCategory,
                     Group, SubGroup, Brand, Company, Supplier, Custodian, AssetRemarks)
from apps.locations.models import Branch, Department, Building, Floor, Room, Region, Site, Location, SubLocation
from django.utils.translation import gettext_lazy as _

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        exclude = ['organization', 'created_by', 'is_deleted', 'custom_fields', 'asset_tag']
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
            'custom_asset_tag': forms.TextInput(attrs={'placeholder': 'e.g. TAG-123'}),
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
                                self.fields['parent'].queryset = Asset.objects.filter(id=parent_id)
                        except (ValueError, TypeError):
                            pass  # invalid input from the client; ignore and fallback to empty queryset
                    elif self.instance.pk and self.instance.parent:
                        self.fields['parent'].queryset = Asset.objects.filter(pk=self.instance.parent.pk)
        except Exception:
            import traceback
            print("ERROR in AssetForm.__init__:")
            print(traceback.format_exc())
            raise

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
    csv_file = forms.FileField(
        label="Select CSV File",
        help_text="Required: name, asset_tag, category_code. Optional: status, price, brand, model, serial_number, branch, building, floor, room, vendor"
    )

    def clean_csv_file(self):
        csv_file = self.cleaned_data['csv_file']
        if not csv_file.name.endswith('.csv'):
            raise forms.ValidationError("Only CSV files are allowed.")
        return csv_file

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
