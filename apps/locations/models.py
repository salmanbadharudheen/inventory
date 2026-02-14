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

# New Location Hierarchy Models

class Region(TenantAwareModel):
    """Top-level location hierarchy"""
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Regions"
        unique_together = ('organization', 'name')
    
    def __str__(self):
        return self.name

class Site(TenantAwareModel):
    """Sites filtered by Region"""
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='sites')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Sites"
        unique_together = ('region', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.region.name})"

class Location(TenantAwareModel):
    """Locations filtered by Site/Building"""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name='locations')
    building = models.ForeignKey(Building, on_delete=models.SET_NULL, null=True, blank=True, related_name='locations')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Locations"
        unique_together = ('site', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.site.name})"

class SubLocation(TenantAwareModel):
    """Sub-locations filtered by Location"""
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='sublocations')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Sub Locations"
        unique_together = ('location', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.location.name})"
