from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
	list_display = ['username', 'email', 'role', 'organization', 'is_staff', 'is_superuser']
	list_filter = ['role', 'organization', 'is_staff', 'is_superuser', 'is_active']
	search_fields = ['username', 'email', 'first_name', 'last_name', 'employee_id']

	fieldsets = DjangoUserAdmin.fieldsets + (
		('Organization Access', {
			'fields': ('role', 'organization', 'branch', 'department', 'designation', 'employee_id')
		}),
	)

	add_fieldsets = DjangoUserAdmin.add_fieldsets + (
		('Organization Access', {
			'classes': ('wide',),
			'fields': ('role', 'organization', 'branch', 'department', 'designation', 'employee_id'),
		}),
	)
