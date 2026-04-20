from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from apps.users.models import User
from apps.assets.models import Asset, Group, SubGroup, Category, SubCategory, Company, Supplier, Brand, Custodian, Vendor, AssetRemarks
from apps.locations.models import Branch, Department, Building, Floor, Room, Region, Site, Location, SubLocation


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'organization', 'branch', 'department',
            'designation', 'employee_id', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid username or password.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include "username" and "password".')


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, label='Confirm Password', style={'input_type': 'password'})
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password2',
            'first_name', 'last_name', 'role', 'organization',
            'branch', 'department', 'designation', 'employee_id'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True}
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        # Run Django's AUTH_PASSWORD_VALIDATORS against the password
        validate_password(attrs['password'], user=User(**{k: v for k, v in attrs.items() if k not in ('password', 'password2')}))
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    old_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password2 = serializers.CharField(required=True, write_only=True, label='Confirm New Password', style={'input_type': 'password'})
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Old password is incorrect.')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "New password fields didn't match."})
        # Run Django's AUTH_PASSWORD_VALIDATORS against the new password
        validate_password(attrs['new_password'], user=self.context['request'].user)
        return attrs


# ─────────────────────────────────────────────
# Lightweight read serializers for FK lookups
# ─────────────────────────────────────────────

class _MiniSerializer(serializers.Serializer):
    """Base for id+name lookup items."""
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class GroupLookupSerializer(_MiniSerializer):
    code = serializers.CharField(read_only=True)


class SubGroupLookupSerializer(_MiniSerializer):
    group = serializers.PrimaryKeyRelatedField(read_only=True)


class CategoryLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'code', 'useful_life_years', 'depreciation_method', 'default_salvage_value']
        read_only_fields = fields


class SubCategoryLookupSerializer(_MiniSerializer):
    category = serializers.PrimaryKeyRelatedField(read_only=True)


class CompanyLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'code']
        read_only_fields = fields


class BranchLookupSerializer(_MiniSerializer):
    pass


class DepartmentLookupSerializer(_MiniSerializer):
    branch = serializers.PrimaryKeyRelatedField(read_only=True)


class RegionLookupSerializer(_MiniSerializer):
    code = serializers.CharField(read_only=True)


class SiteLookupSerializer(_MiniSerializer):
    region = serializers.PrimaryKeyRelatedField(read_only=True)


class BuildingLookupSerializer(_MiniSerializer):
    site = serializers.PrimaryKeyRelatedField(read_only=True)


class FloorLookupSerializer(_MiniSerializer):
    building = serializers.PrimaryKeyRelatedField(read_only=True)


# ─────────────────────────────────────────────
# Asset serializers
# ─────────────────────────────────────────────

class AssetListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views – NO depreciation computation."""
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    company_name = serializers.CharField(source='company.name', read_only=True, default='')
    site_name = serializers.CharField(source='site.name', read_only=True, default='')
    building_name = serializers.CharField(source='building.name', read_only=True, default='')
    department_name = serializers.CharField(source='department.name', read_only=True, default='')
    assigned_to_name = serializers.SerializerMethodField()

    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'asset_tag', 'serial_number',
            'category', 'category_name',
            'company', 'company_name',
            'department', 'department_name',
            'site', 'site_name', 'building', 'building_name',
            'assigned_to', 'assigned_to_name',
            'status', 'condition', 'asset_type',
            'purchase_date', 'purchase_price', 'currency',
            'created_at',
        ]
        read_only_fields = fields

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip() or obj.assigned_to.username
        return ''


class AssetReadSerializer(serializers.ModelSerializer):
    """Full serializer for detail / create response views."""
    category_name = serializers.CharField(source='category.name', read_only=True, default='')
    group_name = serializers.CharField(source='group.name', read_only=True, default='')
    company_name = serializers.CharField(source='company.name', read_only=True, default='')
    site_name = serializers.CharField(source='site.name', read_only=True, default='')
    building_name = serializers.CharField(source='building.name', read_only=True, default='')
    department_name = serializers.CharField(source='department.name', read_only=True, default='')
    assigned_to_name = serializers.SerializerMethodField()
    current_value = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    accumulated_depreciation = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)

    class Meta:
        model = Asset
        fields = [
            'id', 'name', 'description', 'short_description',
            'asset_tag', 'asset_code', 'erp_asset_number',
            'serial_number', 'quantity', 'label_type',
            # classification
            'category', 'category_name', 'sub_category',
            'group', 'group_name', 'sub_group',
            'asset_type', 'brand', 'model', 'condition',
            # ownership
            'company', 'company_name', 'department', 'department_name',
            'assigned_to', 'assigned_to_name',
            'supplier', 'custodian', 'employee_number', 'cost_center',
            # location
            'region', 'site', 'site_name', 'building', 'building_name',
            'floor', 'room', 'location', 'sub_location', 'branch',
            # financial
            'vendor', 'purchase_date', 'purchase_price', 'currency',
            'invoice_number', 'salvage_value', 'useful_life_years',
            'depreciation_method', 'current_value', 'accumulated_depreciation',
            # dates
            'warranty_start', 'warranty_end',
            'po_number', 'po_date', 'do_number', 'do_date',
            'invoice_date', 'date_placed_in_service', 'tagged_date',
            'grn_number',
            # maintenance
            'maintenance_required', 'maintenance_frequency_days', 'next_maintenance_date',
            # status & notes
            'status', 'notes',
            # images
            'image', 'barcode_image', 'qr_code_image',
            # meta
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'asset_tag', 'barcode_image', 'qr_code_image',
            'current_value', 'accumulated_depreciation',
            'created_at', 'updated_at',
        ]

    def get_assigned_to_name(self, obj):
        if obj.assigned_to:
            return f"{obj.assigned_to.first_name} {obj.assigned_to.last_name}".strip() or obj.assigned_to.username
        return ''


class AssetCreateSerializer(serializers.ModelSerializer):
    """
    Write serializer for creating an asset.
    Only accepts the fields that the user should supply.
    organization, created_by, asset_tag are set automatically.
    """

    class Meta:
        model = Asset
        fields = [
            # identification
            'name', 'description', 'short_description',
            'asset_code', 'erp_asset_number',
            'serial_number', 'quantity', 'label_type',
            # classification
            'category', 'sub_category', 'group', 'sub_group',
            'asset_type', 'brand', 'model', 'condition',
            # ownership
            'company', 'department', 'assigned_to',
            'supplier', 'custodian', 'employee_number', 'cost_center',
            # location
            'region', 'site', 'building', 'floor', 'room',
            'location', 'sub_location', 'branch',
            # financial
            'vendor', 'purchase_date', 'purchase_price', 'currency',
            'invoice_number', 'salvage_value', 'useful_life_years',
            'depreciation_method',
            # dates
            'warranty_start', 'warranty_end',
            'po_number', 'po_date', 'do_number', 'do_date',
            'invoice_date', 'date_placed_in_service', 'tagged_date',
            'grn_number',
            # maintenance
            'maintenance_required', 'maintenance_frequency_days', 'next_maintenance_date',
            # status & notes
            'status', 'notes',
            # image (single for mobile)
            'image',
        ]
        extra_kwargs = {
            'name': {'required': True},
            'category': {'required': True},
            'asset_code': {'required': True},
        }

    def validate_asset_code(self, value):
        if not value:
            raise serializers.ValidationError('Asset Code is required.')
        org = self.context['request'].user.organization
        qs = Asset.objects.filter(organization=org, asset_code=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
                raise serializers.ValidationError('An asset with this Asset Code already exists.')
        return value
