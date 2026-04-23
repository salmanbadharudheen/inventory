from django.contrib import admin

from .models import Organization


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
	list_display = ['name', 'slug', 'created_at', 'tag_sequence_format', 'label_template']
	search_fields = ['name', 'slug']
	list_filter = ['tag_sequence_format', 'label_template', 'created_at']
	readonly_fields = ['created_at']

	def has_add_permission(self, request):
		return False

	def has_delete_permission(self, request, obj=None):
		return False
