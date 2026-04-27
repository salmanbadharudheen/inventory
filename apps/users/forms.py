from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import Organization

User = get_user_model()

class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

        # If creator already belongs to an organization, lock new user to that org.
        # This prevents admins from creating users under other organizations.
        if current_user and getattr(current_user, 'organization', None):
            self.fields.pop('organization', None)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'organization', 'branch', 'department']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'organization': forms.Select(attrs={'class': 'form-control'}),
            'branch': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class AdminCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = ['username', 'email', 'first_name', 'last_name', 'organization']
        # Branch/Dept are usually not required for global admins, but depending on logic.
        # Role is excluded from fields to avoid user changing it, we set it in init or save.
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force role to ADMIN and hide/disable it if it was in fields, but we removed it from Meta fields
        # If we need organization, we keep it.

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.ADMIN
        user.is_superuser = False
        if commit:
            user.save()
        return user


class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'slug', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Organization name is required.')
        return name

    def clean_slug(self):
        slug = (self.cleaned_data.get('slug') or '').strip()
        name = (self.cleaned_data.get('name') or '').strip()
        if not slug and name:
            slug = slugify(name)
        if not slug:
            raise forms.ValidationError('Slug is required.')

        queryset = Organization.objects.filter(slug=slug)
        if self.instance and self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError('This slug is already in use.')
        return slug


class AssignOrganizationAdminForm(forms.Form):
    MODE_CHOICES = [
        ('existing', 'Assign Existing User'),
        ('create', 'Create New Admin User'),
    ]
    
    mode = forms.ChoiceField(
        choices=MODE_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input', 'id': 'admin_mode'}),
        initial='existing',
        help_text='Choose whether to assign an existing user or create a new admin user.',
    )
    
    # For existing user assignment
    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Selected user will be assigned to this organization and promoted to Admin role.',
        required=False,
    )

    # For creating new admin user
    new_username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
        required=False,
        help_text='Username for the new admin.',
    )
    new_email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        required=False,
        help_text='Email address for the new admin.',
    )
    new_first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
        required=False,
    )
    new_last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        required=False,
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        required=False,
        help_text='Temporary password for the new admin.',
    )
    new_confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('org', None)
        self.org = org
        super().__init__(*args, **kwargs)
        qs = User.objects.filter(is_superuser=False).order_by('username')
        if org is not None:
            # Allow unassigned users or users already in this organization.
            qs = qs.filter(Q(organization__isnull=True) | Q(organization=org))
        self.fields['user'].queryset = qs

    def clean_new_username(self):
        mode = self.cleaned_data.get('mode')
        username = (self.cleaned_data.get('new_username') or '').strip()
        
        if mode == 'create':
            if not username:
                raise forms.ValidationError('Username is required when creating a new admin.')
            if User.objects.filter(username=username).exists():
                raise forms.ValidationError('This username is already in use.')
        return username

    def clean_new_email(self):
        mode = self.cleaned_data.get('mode')
        email = (self.cleaned_data.get('new_email') or '').strip()
        
        if mode == 'create':
            if not email:
                raise forms.ValidationError('Email is required when creating a new admin.')
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError('This email is already in use.')
        return email

    def clean_new_password(self):
        mode = self.cleaned_data.get('mode')
        password = self.cleaned_data.get('new_password')
        
        if mode == 'create':
            if not password:
                raise forms.ValidationError('Password is required when creating a new admin.')
            if len(password) < 8:
                raise forms.ValidationError('Password must be at least 8 characters long.')
        return password

    def clean(self):
        cleaned_data = super().clean()
        mode = cleaned_data.get('mode')
        
        if mode == 'existing':
            user = cleaned_data.get('user')
            if not user:
                raise forms.ValidationError('Please select a user to assign as admin.')
        
        elif mode == 'create':
            password = cleaned_data.get('new_password')
            confirm_password = cleaned_data.get('new_confirm_password')
            
            if password and password != confirm_password:
                raise forms.ValidationError('Passwords do not match.')
        
        return cleaned_data

    def save(self, commit=True):
        """Returns the user object (either existing or newly created)"""
        mode = self.cleaned_data.get('mode')
        
        if mode == 'existing':
            user = self.cleaned_data.get('user')
        else:  # create
            user = User.objects.create_user(
                username=self.cleaned_data.get('new_username'),
                email=self.cleaned_data.get('new_email'),
                password=self.cleaned_data.get('new_password'),
                first_name=self.cleaned_data.get('new_first_name') or '',
                last_name=self.cleaned_data.get('new_last_name') or '',
                organization=self.org,
                role=User.Role.ADMIN,
                is_superuser=False,
            )
        
        return user


class OrganizationCreateWithAdminForm(OrganizationForm):
    admin_username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Username for this organization admin.',
    )
    admin_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    admin_first_name = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    admin_last_name = forms.CharField(
        required=False,
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    admin_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Temporary password for organization admin.',
    )
    admin_confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    def clean_admin_username(self):
        username = (self.cleaned_data.get('admin_username') or '').strip()
        if not username:
            raise forms.ValidationError('Admin username is required.')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already in use.')
        return username

    def clean_admin_email(self):
        email = (self.cleaned_data.get('admin_email') or '').strip()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already in use.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('admin_password')
        confirm_password = cleaned_data.get('admin_confirm_password')
        if password != confirm_password:
            self.add_error('admin_confirm_password', 'Passwords do not match.')
        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        if not commit:
            raise ValueError('OrganizationCreateWithAdminForm.save requires commit=True')

        organization = super().save(commit=True)
        admin_user = User(
            username=self.cleaned_data['admin_username'],
            email=self.cleaned_data.get('admin_email', ''),
            first_name=self.cleaned_data.get('admin_first_name', ''),
            last_name=self.cleaned_data.get('admin_last_name', ''),
            role=User.Role.ADMIN,
            organization=organization,
            is_superuser=False,
            is_staff=False,
        )
        admin_user.set_password(self.cleaned_data['admin_password'])
        admin_user.save()
        return organization
