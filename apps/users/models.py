from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        FINANCE = 'FINANCE', _('Finance')
        ASSET_MANAGER = 'ASSET_MANAGER', _('Asset Manager')
        AUDITOR = 'AUDITOR', _('Auditor')
        DEPT_MANAGER = 'DEPT_MANAGER', _('Department Manager')
        EMPLOYEE = 'EMPLOYEE', _('Employee')

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.EMPLOYEE)
    organization = models.ForeignKey('core.Organization', on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    branch = models.ForeignKey('locations.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    department = models.ForeignKey('locations.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    
    # Employee Helper Fields
    designation = models.CharField(max_length=255, blank=True)
    employee_id = models.CharField(max_length=100, blank=True, unique=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_auditor(self):
        return self.role == self.Role.AUDITOR

    @property
    def is_asset_manager(self):
        return self.role == self.Role.ASSET_MANAGER
