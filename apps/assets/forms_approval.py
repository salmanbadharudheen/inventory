"""Forms for asset approval workflows"""
from django import forms
from .models import ApprovalRequest, Category
from apps.locations.models import Department
from django.utils.translation import gettext_lazy as _


class AssetApprovalRequestForm(forms.ModelForm):
    """Form for users to submit a request for a new asset"""
    
    class Meta:
        model = ApprovalRequest
        fields = [
            'request_type',
            'comments'
        ]
        widgets = {
            'request_type': forms.Select(attrs={'class': 'form-control'}),
            'comments': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Describe the asset and reason for request'
            }),
        }
    
    # Asset details fields (not stored in ApprovalRequest but in the `data` JSONField)
    asset_name = forms.CharField(
        max_length=255, 
        required=True, 
        label='Asset Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Asset name/description'
        })
    )
    
    asset_category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=True,
        label='Category',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    asset_description = forms.CharField(
        max_length=1000, 
        required=False, 
        label='Description',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'rows': 3, 
            'placeholder': 'Specifications, model, features, etc.'
        })
    )
    
    asset_cost = forms.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        required=False,
        label='Estimated Cost',
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': '0.00', 
            'min': '0', 
            'step': '0.01'
        })
    )
    
    asset_quantity = forms.IntegerField(
        min_value=1,
        required=True,
        label='Quantity',
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'min': '1', 
            'value': '1'
        })
    )
    
    asset_reason = forms.CharField(
        max_length=500,
        required=True,
        label='Reason for Request',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': 'Why is this asset needed?'
        })
    )
    
    asset_department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        required=False,
        label='Department',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    requested_by = forms.CharField(
        max_length=255,
        required=False,
        label='Requested By',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Name of person requesting this asset'
        })
    )
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Only show relevant request types for asset creation
        self.fields['request_type'].choices = [
            (ApprovalRequest.RequestType.ASSET_CREATE, _('New Asset Request')),
        ]
        
        # Filter dropdowns by organization
        if self.request and hasattr(self.request.user, 'organization') and self.request.user.organization:
            org = self.request.user.organization
            self.fields['asset_category'].queryset = Category.objects.filter(organization=org)
            self.fields['asset_department'].queryset = Department.objects.filter(branch__organization=org)
    
    def clean(self):
        cleaned_data = super().clean()
        asset_quantity = cleaned_data.get('asset_quantity', 1)
        if asset_quantity < 1:
            self.add_error('asset_quantity', 'Quantity must be at least 1')
        return cleaned_data
