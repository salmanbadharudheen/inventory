from django import forms
from .models import Branch, Department, Building, Floor, Room

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
        if request and hasattr(request.user, 'organization'):
             self.fields['branch'].queryset = Branch.objects.filter(organization=request.user.organization)

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
