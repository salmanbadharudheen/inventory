from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        EMPLOYEE = 'EMPLOYEE', _('Employee')
        CHECKER = 'CHECKER', _('Checker/Manager')
        SENIOR_MANAGER = 'SENIOR_MANAGER', _('Senior Manager')

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
        return False

    @property
    def is_asset_manager(self):
        return False
    @property
    def is_data_entry(self):
        return self.role == self.Role.EMPLOYEE

    @property
    def is_checker(self):
        return self.role == self.Role.CHECKER

    @property
    def is_senior_manager(self):
        return self.role == self.Role.SENIOR_MANAGER

    @property
    def can_approve(self):
        """Check if user can approve requests"""
        return self.role in [self.Role.CHECKER, self.Role.SENIOR_MANAGER, self.Role.ADMIN]

    @property
    def can_final_approve(self):
        """Check if user can do final approval"""
        return self.role in [self.Role.SENIOR_MANAGER, self.Role.ADMIN]