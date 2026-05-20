import os

from django import forms
from django.core.exceptions import ValidationError
from .models import (Asset, AssetAttachment, Vendor, Category, SubCategory,
                     Group, SubGroup, Brand, Company, Supplier, Custodian, AssetRemarks, AssetTransfer, AssetDisposal)
from apps.locations.models import Branch, Department, Building, Floor, Room, Region, Site, Location, SubLocation
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


MAX_IMAGE_UPLOAD_BYTES = 5 * 1024 * 1024   # 5 MB
MAX_DOCUMENT_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}
ALLOWED_DOCUMENT_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.jpg', '.jpeg', '.png', '.webp'
}

LABEL_TYPE_CHOICES = [
    ('RFID', 'RFID'),
    ('QR_CODE', 'QR Code'),
    ('BARCODE', 'Barcode'),
]

class AssetForm(forms.ModelForm):
    label_type = forms.MultipleChoiceField(
        choices=LABEL_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Label Type',
    )
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
            'tagging_status': forms.Select(attrs={'class': 'form-control'}),
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

            # Purchase date is required for asset creation/edit flows.
            if 'purchase_date' in self.fields:
                self.fields['purchase_date'].required = True

            # Set initial for label_type (multi-select from comma-separated string)
            if not self.instance.pk:
                self.initial['label_type'] = ['QR_CODE', 'BARCODE']
            else:
                stored = self.instance.label_type or ''
                self.initial['label_type'] = [v.strip() for v in stored.split(',') if v.strip()]

            # Style all fields (skip CheckboxSelectMultiple)
            for field_name, field in self.fields.items():
                if isinstance(field.widget, forms.CheckboxSelectMultiple):
                    continue
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
                # Default org-wide (AJAX will narrow by region/site as user selects)
                self.fields['site'].queryset = Site.objects.filter(region__organization=org)
                self.fields['location'].queryset = Location.objects.filter(site__region__organization=org)
                self.fields['sub_location'].queryset = SubLocation.objects.filter(location__site__region__organization=org)
                # Narrow site/location/sublocation querysets.
                # On POST (is_bound): include both submitted and instance IDs so that
                # stale child-field values pass Django's field-level validation and
                # reach clean(), where mismatches are detected and cleared.
                # On GET (display): use only the instance's saved values.
                if not self.is_bound:
                    # Display mode: narrow to saved values for efficient dropdowns
                    _r = getattr(self.instance, 'region_id', None)
                    if _r:
                        self.fields['site'].queryset = Site.objects.filter(
                            region_id=_r, region__organization=org)
                        self.fields['location'].queryset = Location.objects.filter(
                            site__region_id=_r, site__region__organization=org)
                        self.fields['sub_location'].queryset = SubLocation.objects.filter(
                            location__site__region_id=_r, location__site__region__organization=org)
                    _s = getattr(self.instance, 'site_id', None)
                    if _s:
                        self.fields['location'].queryset = Location.objects.filter(
                            site_id=_s, site__region__organization=org)
                        self.fields['sub_location'].queryset = SubLocation.objects.filter(
                            location__site_id=_s, location__site__region__organization=org)
                    _l = getattr(self.instance, 'location_id', None)
                    if _l:
                        self.fields['sub_location'].queryset = SubLocation.objects.filter(
                            location_id=_l, location__site__region__organization=org)
                else:
                    # Submission mode: accept both submitted and saved values so clean()
                    # can detect and clear hierarchy mismatches
                    def _ids(*vals):
                        return list({str(v) for v in vals if v})

                    _rids = _ids(self.data.get('region'), getattr(self.instance, 'region_id', None))
                    if _rids:
                        self.fields['site'].queryset = Site.objects.filter(
                            region_id__in=_rids, region__organization=org)
                        self.fields['location'].queryset = Location.objects.filter(
                            site__region_id__in=_rids, site__region__organization=org)
                        self.fields['sub_location'].queryset = SubLocation.objects.filter(
                            location__site__region_id__in=_rids, location__site__region__organization=org)

                    _sids = _ids(self.data.get('site'), getattr(self.instance, 'site_id', None))
                    if _sids:
                        self.fields['location'].queryset = Location.objects.filter(
                            site_id__in=_sids, site__region__organization=org)
                        self.fields['sub_location'].queryset = SubLocation.objects.filter(
                            location__site_id__in=_sids, location__site__region__organization=org)

                    _lids = _ids(self.data.get('location'), getattr(self.instance, 'location_id', None))
                    if _lids:
                        self.fields['sub_location'].queryset = SubLocation.objects.filter(
                            location_id__in=_lids, location__site__region__organization=org)
                self.fields['asset_remarks'].queryset = AssetRemarks.objects.filter(organization=org)

                # Filter assigned_to users by organization
                if 'assigned_to' in self.fields:
                    self.fields['assigned_to'].queryset = User.objects.filter(
                        organization=org, is_active=True
                    ).order_by('first_name', 'last_name', 'username')
                
                # Optimized Parent field for AJAX - prevent loading all assets
                if 'parent' in self.fields:
                    self.fields['parent'].queryset = Asset.objects.none()

                    if 'parent' in self.data:
                        try:
                            parent_id = self.data.get('parent')
                            if parent_id:
                                self.fields['parent'].queryset = Asset.objects.filter(
                                    id=parent_id,
                                    organization=org,
                                    is_deleted=False
                                )
                        except (ValueError, TypeError):
                            pass  # invalid input from the client; ignore and fallback to empty queryset
                    elif self.instance.pk and self.instance.parent:
                        self.fields['parent'].queryset = Asset.objects.filter(
                            pk=self.instance.parent.pk,
                            organization=org,
                            is_deleted=False
                        )
        except Exception:
            import traceback
            print("ERROR in AssetForm.__init__:")
            print(traceback.format_exc())
            raise

    def clean_label_type(self):
        values = self.cleaned_data.get('label_type', [])
        return ','.join(values)

    def clean(self):
        cleaned_data = super().clean()

        if not cleaned_data.get('purchase_date'):
            self.add_error('purchase_date', _('Purchase date is required.'))

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

        # Cross-validate location hierarchy: clear child fields whose parent changed
        region = cleaned_data.get('region')
        site = cleaned_data.get('site')
        location = cleaned_data.get('location')
        sub_location = cleaned_data.get('sub_location')

        # If region changed from the saved value, unconditionally clear all location
        # children so the DB is never left with a site/location from the old region.
        if self.instance.pk:
            inst_region_id = getattr(self.instance, 'region_id', None)
            sub_region_id = getattr(region, 'pk', None) if region else None
            if sub_region_id and inst_region_id and sub_region_id != inst_region_id:
                for _f in ('site', 'location', 'sub_location', 'building', 'floor', 'room'):
                    cleaned_data[_f] = None
                site = None
                location = None
                sub_location = None

        # Site must belong to the selected region
        if site and region and hasattr(site, 'region_id'):
            if site.region_id != region.pk:
                cleaned_data['site'] = None
                cleaned_data['location'] = None
                cleaned_data['sub_location'] = None
                cleaned_data['building'] = None
                cleaned_data['floor'] = None
                cleaned_data['room'] = None
                site = None

        # Location must belong to the selected site
        if location and site and hasattr(location, 'site_id'):
            if location.site_id != site.pk:
                cleaned_data['location'] = None
                cleaned_data['sub_location'] = None
                location = None

        # SubLocation must belong to the selected location
        if sub_location and location and hasattr(sub_location, 'location_id'):
            if sub_location.location_id != location.pk:
                cleaned_data['sub_location'] = None

        return cleaned_data

class AssetAttachmentForm(forms.ModelForm):
    class Meta:
        model = AssetAttachment
        fields = ['file', 'attachment_type', 'description']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['sub_group', 'name', 'useful_life_years', 'depreciation_method', 'default_salvage_value', 'default_expected_units']
        widgets = {
            'sub_group': forms.Select(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Electronics'}),
            'useful_life_years': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'depreciation_method': forms.Select(attrs={'class': 'form-control'}),
            'default_salvage_value': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': '0.00'}),
            'default_expected_units': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Category name is required.')
        
        # Check for duplicate in the same organization (exclude current instance if editing)
        organization = getattr(self.request, 'user', None) and self.request.user.organization
        if organization:
            qs = Category.objects.filter(organization=organization, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'A category with the name "{name}" already exists in your organization.')
        
        return name
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.request and hasattr(self.request.user, 'organization') and self.request.user.organization:
            org = self.request.user.organization
            self.fields['sub_group'].queryset = SubGroup.objects.filter(group__organization=org)
        self.fields['sub_group'].required = False

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
    
    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        name = cleaned_data.get('name', '').strip()
        
        if category and name:
            # Check for duplicate in the same category (exclude current instance if editing)
            qs = SubCategory.objects.filter(category=category, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'A sub-category with the name "{name}" already exists in the "{category.name}" category.')
        
        return cleaned_data

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

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Vendor name is required.')

        organization = getattr(self.request, 'user', None) and self.request.user.organization
        if organization:
            qs = Vendor.objects.filter(organization=organization, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'A vendor with the name "{name}" already exists in your organization.')

        return name

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
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Group name is required.')
        
        # Check for duplicate in the same organization (exclude current instance if editing)
        organization = getattr(self.request, 'user', None) and self.request.user.organization
        if organization:
            qs = Group.objects.filter(organization=organization, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'A group with the name "{name}" already exists in your organization.')
        
        return name

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
    
    def clean(self):
        cleaned_data = super().clean()
        group = cleaned_data.get('group')
        name = cleaned_data.get('name', '').strip()
        
        if group and name:
            # Check for duplicate in the same group (exclude current instance if editing)
            qs = SubGroup.objects.filter(group=group, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'A sub-group with the name "{name}" already exists in the "{group.name}" group.')
        
        return cleaned_data

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Dell'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Brand name is required.')
        
        # Check for duplicate in the same organization (exclude current instance if editing)
        organization = getattr(self.request, 'user', None) and self.request.user.organization
        if organization:
            qs = Brand.objects.filter(organization=organization, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'A brand with the name "{name}" already exists in your organization.')
        
        return name

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

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Company name is required.')

        organization = getattr(self.request, 'user', None) and self.request.user.organization
        if organization:
            qs = Company.objects.filter(organization=organization, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'A company with the name "{name}" already exists in your organization.')

        return name

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
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Supplier name is required.')
        
        # Check for duplicate in the same organization (exclude current instance if editing)
        organization = getattr(self.request, 'user', None) and self.request.user.organization
        if organization:
            qs = Supplier.objects.filter(organization=organization, name__iexact=name)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'A supplier with the name "{name}" already exists in your organization.')
        
        return name

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

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')

        if not user:
            return cleaned_data

        organization = getattr(self.request, 'user', None) and self.request.user.organization
        if organization:
            qs = Custodian.objects.filter(organization=organization, user=user)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error('user', 'This user is already assigned as a custodian in your organization.')

        return cleaned_data

class AssetRemarksForm(forms.ModelForm):
    class Meta:
        model = AssetRemarks
        fields = ['remark', 'description']
        widgets = {
            'remark': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Needs Repair'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def clean_remark(self):
        remark = self.cleaned_data.get('remark', '').strip()
        if not remark:
            raise forms.ValidationError('Remark is required.')

        organization = getattr(self.request, 'user', None) and self.request.user.organization
        if organization:
            qs = AssetRemarks.objects.filter(organization=organization, remark__iexact=remark)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(f'The remark "{remark}" already exists in your organization.')

        return remark

class AssetTransferForm(forms.ModelForm):
    """Form for creating and updating asset transfers"""

    # `asset` is a free-form hidden field carrying either a single asset ID
    # ("5") or a comma-separated list ("5,6,7"). The view parses this manually
    # in form_valid() and creates one AssetTransfer per ID. Declared outside
    # Meta.fields so the ModelForm machinery does NOT try to assign the raw
    # string to the AssetTransfer.asset FK during _post_clean.
    asset = forms.CharField(required=False, widget=forms.HiddenInput())

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
            'transferred_to_location',
            'transferred_to_company',
            'transferred_to_department',
            'transferred_to_custodian',
            'movement_reason',
            'requester_name',
        ]
        widgets = {
            'transfer_no': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Optional transfer reference'}),
            'transfer_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Short description for this transfer'}),
            'transferred_to_region': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_site': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_building': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_floor': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_room': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_location': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_company': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_department': forms.Select(attrs={'class': 'form-control'}),
            'transferred_to_custodian': forms.Select(attrs={'class': 'form-control'}),
            'movement_reason': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Specific reason for this movement'
            }),
            'requester_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Requester name (free text)'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Filter by organization
        if self.request and hasattr(self.request.user, 'organization') and self.request.user.organization:
            org = self.request.user.organization
            # `asset` is a free-form CharField now (parsed manually in view); no queryset to set.

            # Populate base querysets
            self.fields['transferred_to_region'].queryset = Region.objects.filter(organization=org)
            self.fields['transferred_to_site'].queryset = Site.objects.none()
            self.fields['transferred_to_building'].queryset = Building.objects.none()
            self.fields['transferred_to_floor'].queryset = Floor.objects.none()
            self.fields['transferred_to_room'].queryset = Room.objects.none()
            self.fields['transferred_to_location'].queryset = Location.objects.none()
            self.fields['transferred_to_company'].queryset = Company.objects.filter(organization=org)
            self.fields['transferred_to_department'].queryset = Department.objects.filter(branch__organization=org)
            self.fields['transferred_to_custodian'].queryset = Custodian.objects.filter(organization=org)

            region_id = self.data.get('transferred_to_region') or getattr(self.instance, 'transferred_to_region_id', None)

            if self.is_bound:
                # POST submission: use org-wide querysets so any valid org ID passes
                # validation regardless of parent selection order. JS cascade handles UI.
                self.fields['transferred_to_site'].queryset = Site.objects.filter(
                    region__organization=org)
                self.fields['transferred_to_building'].queryset = Building.objects.filter(
                    branch__organization=org)
                self.fields['transferred_to_floor'].queryset = Floor.objects.filter(
                    building__branch__organization=org)
                self.fields['transferred_to_room'].queryset = Room.objects.filter(
                    floor__building__branch__organization=org)
                self.fields['transferred_to_location'].queryset = Location.objects.filter(
                    site__region__organization=org)
            else:
                # GET (initial load / edit): restore cascade from saved instance values
                if region_id:
                    self.fields['transferred_to_site'].queryset = Site.objects.filter(
                        region_id=region_id, region__organization=org)

                site_id = getattr(self.instance, 'transferred_to_site_id', None)
                if site_id:
                    self.fields['transferred_to_building'].queryset = Building.objects.filter(
                        locations__site_id=site_id,
                        locations__site__region__organization=org,
                    ).distinct()

                building_id = getattr(self.instance, 'transferred_to_building_id', None)
                if building_id:
                    self.fields['transferred_to_floor'].queryset = Floor.objects.filter(
                        building_id=building_id, building__branch__organization=org)
                    self.fields['transferred_to_location'].queryset = Location.objects.filter(
                        building_id=building_id, site__region__organization=org)

                floor_id = getattr(self.instance, 'transferred_to_floor_id', None)
                if floor_id:
                    self.fields['transferred_to_room'].queryset = Room.objects.filter(
                        floor_id=floor_id, floor__building__branch__organization=org)
        
        # Make all fields optional (bulk form handles multiple assets via JS)
        self.fields['transfer_no'].required = False
        self.fields['asset'].required = False
        self.fields['transfer_description'].required = False
        self.fields['transferred_to_region'].required = False
        self.fields['transferred_to_site'].required = False
        self.fields['transferred_to_building'].required = False
        self.fields['transferred_to_floor'].required = False
        self.fields['transferred_to_room'].required = False
        self.fields['transferred_to_location'].required = False
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
    """Form for creating disposal requests for one or many assets."""

    # Used when coming from bulk selection on the asset list page.
    asset_ids = forms.CharField(required=False, widget=forms.HiddenInput())

    # Manual selection mode when opening disposal form directly.
    selected_assets = forms.ModelMultipleChoiceField(
        queryset=Asset.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control searchable-select',
            'data-placeholder': 'Search and select assets...'
        })
    )
    
    class Meta:
        model = AssetDisposal
        fields = ['disposal_method', 'reason', 'disposal_date', 'estimated_salvage_value', 'notes']
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

        # Keep initial GET lightweight: do not preload all eligible assets.
        self.fields['selected_assets'].queryset = Asset.objects.none()

        if self.request and self.request.user.is_authenticated and hasattr(self.request.user, 'organization') and self.request.user.organization:
            org = self.request.user.organization
            eligible_qs = Asset.objects.filter(
                organization=org,
                is_deleted=False,
                status__in=[Asset.Status.ACTIVE, Asset.Status.IN_STORAGE, Asset.Status.UNDER_MAINTENANCE]
            )

            # For bound forms (POST), bind queryset to submitted IDs so validation works
            # without loading every eligible asset.
            if self.is_bound:
                selected_key = self.add_prefix('selected_assets')
                submitted_ids = list(dict.fromkeys(self.data.getlist(selected_key)))
                if submitted_ids:
                    self.fields['selected_assets'].queryset = eligible_qs.filter(id__in=submitted_ids)
        
        self.fields['disposal_date'].required = False
        self.fields['estimated_salvage_value'].required = False
        self.fields['reason'].required = False
        self.fields['notes'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        selected_assets = cleaned_data.get('selected_assets')
        asset_ids = (cleaned_data.get('asset_ids') or '').strip()

        # On create, require at least one selected asset. On edit, keep existing asset.
        if not selected_assets and not asset_ids and not (self.instance and self.instance.pk and self.instance.asset_id):
            raise forms.ValidationError('Please select at least one asset for disposal.')

        return cleaned_data


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