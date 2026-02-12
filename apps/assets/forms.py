from django import forms
from .models import Asset, AssetAttachment, Vendor, Category, SubCategory
from apps.locations.models import Branch, Department, Building, Floor, Room
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
            'notes': forms.Textarea(attrs={'rows': 3}),
            'useful_life_years': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Optional'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Style all fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field.required:
                field.widget.attrs['class'] += ' required'
        
        # Filter dropdowns by Organization if user is logged in
        if self.request and self.request.user.organization:
            org = self.request.user.organization
            self.fields['category'].queryset = Category.objects.filter(organization=org)
            self.fields['sub_category'].queryset = SubCategory.objects.filter(category__organization=org)
            self.fields['branch'].queryset = Branch.objects.filter(organization=org)
            self.fields['department'].queryset = Department.objects.filter(branch__organization=org)
            self.fields['building'].queryset = Building.objects.filter(branch__organization=org)
            self.fields['floor'].queryset = Floor.objects.filter(building__branch__organization=org)
            self.fields['room'].queryset = Room.objects.filter(floor__building__branch__organization=org)
            self.fields['vendor'].queryset = Vendor.objects.filter(organization=org)

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
