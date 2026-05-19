from django import forms
from .models import Branch, Department, Building, Floor, Room, Region, Site, Location, SubLocation

class BranchForm(forms.ModelForm):
    class Meta:
        model = Branch
        fields = ['name', 'code', 'address', 'country', 'currency']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Main Headquarters'}),
            'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. HQ'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'country': forms.TextInput(attrs={'class': 'form-input'}),
            'currency': forms.TextInput(attrs={'class': 'form-input'}),
        }

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'branch']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. IT Department'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        self.request = request
        if request and hasattr(request.user, 'organization'):
             self.fields['branch'].queryset = Branch.objects.filter(organization=request.user.organization)

    def clean_name(self):
        name = self.cleaned_data.get('name', '')
        return name.strip()

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        branch = cleaned_data.get('branch')

        if not name or not branch:
            return cleaned_data

        org = None
        if self.request and hasattr(self.request.user, 'organization'):
            org = self.request.user.organization
        elif self.instance and self.instance.pk:
            org = self.instance.organization

        duplicate_qs = Department.objects.filter(
            organization=org,
            branch=branch,
            name__iexact=name,
        )

        if self.instance and self.instance.pk:
            duplicate_qs = duplicate_qs.exclude(pk=self.instance.pk)

        if duplicate_qs.exists():
            self.add_error('name', 'This department already exists in the selected branch.')

        return cleaned_data

class BuildingForm(forms.ModelForm):
    class Meta:
        model = Building
        fields = ['name', 'branch']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Building A'}),
            'branch': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request and hasattr(request.user, 'organization'):
            self.fields['branch'].queryset = Branch.objects.filter(organization=request.user.organization)

class FloorForm(forms.ModelForm):
    class Meta:
        model = Floor
        fields = ['name', 'building']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 1st Floor'}),
            'building': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request and hasattr(request.user, 'organization'):
            self.fields['building'].queryset = Building.objects.filter(branch__organization=request.user.organization)

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'floor']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Room 101'}),
            'floor': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request and hasattr(request.user, 'organization'):
            self.fields['floor'].queryset = Floor.objects.filter(building__branch__organization=request.user.organization)

# New Location Hierarchy Forms

class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['name', 'code', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., North Region'}),
            'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }

class SiteForm(forms.ModelForm):
    class Meta:
        model = Site
        fields = ['region', 'name', 'code', 'address']
        widgets = {
            'region': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Main Site'}),
            'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request and hasattr(request.user, 'organization'):
            self.fields['region'].queryset = Region.objects.filter(organization=request.user.organization)

class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['site', 'building', 'name', 'code', 'description']
        widgets = {
            'site': forms.Select(attrs={'class': 'form-select'}),
            'building': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Warehouse A'}),
            'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request and hasattr(request.user, 'organization'):
            self.fields['site'].queryset = Site.objects.filter(region__organization=request.user.organization)
            self.fields['building'].queryset = Building.objects.filter(branch__organization=request.user.organization)

class SubLocationForm(forms.ModelForm):
    class Meta:
        model = SubLocation
        fields = ['location', 'name', 'code', 'description']
        widgets = {
            'location': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., Section A1'}),
            'code': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Optional'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if request and hasattr(request.user, 'organization'):
            self.fields['location'].queryset = Location.objects.filter(site__region__organization=request.user.organization)
