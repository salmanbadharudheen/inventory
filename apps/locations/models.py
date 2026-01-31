from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TenantAwareModel

class Branch(TenantAwareModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    address = models.TextField(blank=True)
    country = models.CharField(max_length=100, default='USA')
    currency = models.CharField(max_length=10, default='USD')

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        verbose_name_plural = "Branches"
        unique_together = ['organization', 'code']

class Department(TenantAwareModel):
    name = models.CharField(max_length=255)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='departments')

    def __str__(self):
        return f"{self.name} - {self.branch.code}"

class Building(TenantAwareModel):
    name = models.CharField(max_length=255)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='buildings')
    
    def __str__(self):
        return f"{self.name} ({self.branch.name})"

class Floor(TenantAwareModel):
    name = models.CharField(max_length=50)
    building = models.ForeignKey(Building, on_delete=models.CASCADE, related_name='floors')
    
    def __str__(self):
        return f"{self.name} - {self.building.name}"

class Room(TenantAwareModel):
    name = models.CharField(max_length=100)
    floor = models.ForeignKey(Floor, on_delete=models.CASCADE, related_name='rooms')
    
    def __str__(self):
        return f"{self.name} - {self.floor.name}"
