from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.core.models import TenantAwareModel
import uuid
from datetime import date
from decimal import Decimal

class DepreciationMethod(models.TextChoices):
    STRAIGHT_LINE = 'STRAIGHT_LINE', _('Straight Line')
    REDUCING_BALANCE = 'REDUCING_BALANCE', _('Reducing Balance')

class Vendor(TenantAwareModel):
    name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    
    def __str__(self):
        return self.name

class Category(TenantAwareModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50) # e.g. IT, FUR
    useful_life_years = models.PositiveIntegerField(default=5)
    depreciation_method = models.CharField(
        max_length=50, 
        choices=DepreciationMethod.choices, 
        default=DepreciationMethod.STRAIGHT_LINE
    )
    
    class Meta:
        unique_together = ('organization', 'code')
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class SubCategory(TenantAwareModel):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    name = models.CharField(max_length=255)
    
    class Meta:
        verbose_name_plural = "Sub Categories"
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"

def generate_asset_tag(organization):
    """
    Generate sequential asset tag for an organization.
    Format: AST-00001, AST-00002, etc.
    """
    from django.db.models import Max
    # Get the last asset tag for this organization
    last_asset = Asset.objects.filter(organization=organization, asset_tag__startswith='AST-').aggregate(Max('asset_tag'))
    last_tag = last_asset['asset_tag__max']
    
    if last_tag:
        # Extract the number from the last tag (e.g., "AST-00005" -> 5)
        try:
            last_number = int(last_tag.split('-')[1])
            new_number = last_number + 1
        except (IndexError, ValueError):
            new_number = 1
    else:
        new_number = 1
    
    # Format as AST-00001
    return f"AST-{new_number:05d}"

class Asset(TenantAwareModel):
    # Enums
    class Type(models.TextChoices):
        PHYSICAL = 'PHYSICAL', _('Physical')
        DIGITAL = 'DIGITAL', _('Digital')
        LICENSE = 'LICENSE', _('License')

    class Condition(models.TextChoices):
        NEW = 'NEW', _('New')
        USED = 'USED', _('Used')
        DAMAGED = 'DAMAGED', _('Damaged')
        UNDER_REPAIR = 'UNDER_REPAIR', _('Under Repair')

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        IN_STORAGE = 'IN_STORAGE', _('In Storage')
        UNDER_MAINTENANCE = 'UNDER_MAINTENANCE', _('Under Maintenance')
        LOST = 'LOST', _('Lost')
        STOLEN = 'STOLEN', _('Stolen')
        RETIRED = 'RETIRED', _('Retired')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # A) Identification
    name = models.CharField(max_length=255)
    asset_tag = models.CharField(max_length=100, help_text="Unique Asset Code")
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    sub_category = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    asset_type = models.CharField(max_length=20, choices=Type.choices, default=Type.PHYSICAL)
    
    brand = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    condition = models.CharField(max_length=20, choices=Condition.choices, default=Condition.NEW)

    # B) Ownership
    department = models.ForeignKey('locations.Department', on_delete=models.SET_NULL, null=True, blank=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_assets')
    cost_center = models.CharField(max_length=100, blank=True)

    # C) Location
    branch = models.ForeignKey('locations.Branch', on_delete=models.SET_NULL, null=True, blank=True)
    building = models.ForeignKey('locations.Building', on_delete=models.SET_NULL, null=True, blank=True)
    floor = models.ForeignKey('locations.Floor', on_delete=models.SET_NULL, null=True, blank=True)
    room = models.ForeignKey('locations.Room', on_delete=models.SET_NULL, null=True, blank=True)

    # D) Financial
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default='AED', blank=True)
    invoice_number = models.CharField(max_length=100, blank=True)
    
    warranty_start = models.DateField(null=True, blank=True)
    warranty_end = models.DateField(null=True, blank=True)
    
    depreciation_method = models.CharField(max_length=50, choices=DepreciationMethod.choices, default=DepreciationMethod.STRAIGHT_LINE, blank=True)
    useful_life_years = models.PositiveIntegerField(default=5, blank=True)
    salvage_value = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)

    # E) Maintenance
    maintenance_required = models.BooleanField(default=False)
    maintenance_frequency_days = models.PositiveIntegerField(default=0, help_text="Frequency in days", blank=True)
    next_maintenance_date = models.DateField(null=True, blank=True)
    
    # F) Compliance & Extras
    notes = models.TextField(blank=True)
    custom_fields = models.JSONField(default=dict, blank=True)

    # G) Status
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.ACTIVE)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_assets')

    @property
    def accumulated_depreciation(self):
        if not self.purchase_price or not self.purchase_date:
            return Decimal('0.00')
        
        years_passed = (date.today() - self.purchase_date).days / 365.25
        if years_passed <= 0:
            return Decimal('0.00')
        
        # Cap years passed at useful life
        years_passed = min(years_passed, self.useful_life_years)
        
        if self.depreciation_method == DepreciationMethod.STRAIGHT_LINE:
            annual_dep = (self.purchase_price - self.salvage_value) / self.useful_life_years
            acc_dep = annual_dep * Decimal(str(years_passed))
            return acc_dep.quantize(Decimal('0.01'))
        
        elif self.depreciation_method == DepreciationMethod.REDUCING_BALANCE:
            # Rate = 1 - (Salvage/Cost)^(1/Life)
            if self.salvage_value > 0:
                rate = 1 - (float(self.salvage_value) / float(self.purchase_price)) ** (1.0 / self.useful_life_years)
                current_val = float(self.purchase_price) * ((1 - rate) ** years_passed)
                acc_dep = float(self.purchase_price) - current_val
                return Decimal(str(acc_dep)).quantize(Decimal('0.01'))
            else:
                # If salvage is 0, reducing balance usually needs a floor or different formula
                # Using a 20% default rate if salvage is 0 to avoid log/root errors
                rate = 0.20 
                current_val = float(self.purchase_price) * ((1 - rate) ** years_passed)
                acc_dep = float(self.purchase_price) - current_val
                return Decimal(str(acc_dep)).quantize(Decimal('0.01'))
        
        return Decimal('0.00')

    @property
    def current_value(self):
        if not self.purchase_price:
            return Decimal('0.00')
        val = self.purchase_price - self.accumulated_depreciation
        return val.quantize(Decimal('0.01'))

    def get_depreciation_schedule(self):
        if not self.purchase_price or not self.purchase_date:
            return []
            
        schedule = []
        cost = self.purchase_price
        salvage = self.salvage_value
        life = self.useful_life_years
        
        if self.depreciation_method == DepreciationMethod.STRAIGHT_LINE:
            annual_dep = (cost - salvage) / life
            for year in range(life + 1):
                dep = annual_dep if year > 0 else Decimal('0.00')
                acc_dep = min(annual_dep * year, cost - salvage)
                nbv = cost - acc_dep
                schedule.append({
                    'year': year,
                    'year_date': self.purchase_date.year + year,
                    'depreciation': dep.quantize(Decimal('0.01')),
                    'accumulated': acc_dep.quantize(Decimal('0.01')),
                    'nbv': nbv.quantize(Decimal('0.01'))
                })
        
        elif self.depreciation_method == DepreciationMethod.REDUCING_BALANCE:
            if salvage > 0:
                rate = 1 - (float(salvage) / float(cost)) ** (1.0 / life)
            else:
                rate = 0.20
                
            current_nbv = float(cost)
            acc_dep = 0.0
            for year in range(life + 1):
                if year == 0:
                    dep = 0.0
                else:
                    dep = current_nbv * rate
                    # Ensure we don't go below salvage
                    if current_nbv - dep < float(salvage):
                        dep = current_nbv - float(salvage)
                    
                    current_nbv -= dep
                    acc_dep += dep

                schedule.append({
                    'year': year,
                    'year_date': self.purchase_date.year + year,
                    'depreciation': Decimal(str(dep)).quantize(Decimal('0.01')),
                    'accumulated': Decimal(str(acc_dep)).quantize(Decimal('0.01')),
                    'nbv': Decimal(str(current_nbv)).quantize(Decimal('0.01'))
                })
                
        return schedule

    def save(self, *args, **kwargs):
        # Inherit depreciation rules from category if not explicitly set
        if self.category:
            # If it's a new asset and life/method are at defaults, pull from category
            if self._state.adding:
                if self.useful_life_years == 5: # Default value
                    self.useful_life_years = self.category.useful_life_years
                if self.depreciation_method == DepreciationMethod.STRAIGHT_LINE:
                    self.depreciation_method = self.category.depreciation_method
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.asset_tag})"

    class Meta:
        unique_together = [('organization', 'asset_tag')]
        indexes = [
            models.Index(fields=['asset_tag']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['status']),
            models.Index(fields=['organization']),
            models.Index(fields=['organization', 'category']),
            models.Index(fields=['organization', 'assigned_to']),
        ]

class AssetAttachment(TenantAwareModel):
    class Type(models.TextChoices):
        INVOICE = 'INVOICE', _('Invoice')
        MANUAL = 'MANUAL', _('Manual')
        WARRANTY = 'WARRANTY', _('Warranty')
        PHOTO = 'PHOTO', _('Photo')
        OTHER = 'OTHER', _('Other')

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='assets/attachments/')
    attachment_type = models.CharField(max_length=20, choices=Type.choices, default=Type.OTHER)
    description = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.get_attachment_type_display()} - {self.asset.asset_tag}"

class AssetActivityLog(TenantAwareModel):
    class Action(models.TextChoices):
        CREATE = 'CREATE', _('Create')
        UPDATE = 'UPDATE', _('Update')
        ASSIGN = 'ASSIGN', _('Assign')
        TRANSFER = 'TRANSFER', _('Transfer')
        RETIRE = 'RETIRE', _('Retire')
        DELETE = 'DELETE', _('Delete')

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='activity_logs')
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action_type = models.CharField(max_length=20, choices=Action.choices)
    details = models.JSONField(default=dict, help_text="Stores changed fields or diff")
    
    def __str__(self):
        return f"{self.asset.asset_tag} - {self.action_type}"
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Category)
def create_default_subcategory(sender, instance, created, **kwargs):
    if created:
        SubCategory.objects.create(
            category=instance,
            name="General"
        )
