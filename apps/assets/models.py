from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.core.models import TenantAwareModel
import uuid
from datetime import date
from decimal import Decimal
from django.utils.text import slugify

class DepreciationMethod(models.TextChoices):
    STRAIGHT_LINE = 'STRAIGHT_LINE', _('Straight Line')
    DOUBLE_DECLINING = 'DOUBLE_DECLINING', _('Double Declining Balance')
    SYD = 'SYD', _('Sum of Years Digits')
    UNITS_OF_PRODUCTION = 'UNITS_OF_PRODUCTION', _('Units of Production')

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
    code = models.CharField(max_length=50, blank=True)  # Auto-generated

    useful_life_years = models.PositiveIntegerField(default=5) # Required now
    
    depreciation_method = models.CharField(
        max_length=50,
        choices=DepreciationMethod.choices,
        default=DepreciationMethod.STRAIGHT_LINE
    )

    default_salvage_value = models.DecimalField(max_digits=12, decimal_places=2, default=0, blank=True)
    default_expected_units = models.PositiveBigIntegerField(null=True, blank=True)  # only for UoP

    class Meta:
        unique_together = ('organization', 'code')
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.code:
            # --- Auto-generate code: <3-letter prefix><3-digit number> ---

            # 1. Extract only alphabetic chars, uppercase, first 3
            alpha_chars = ''.join(c for c in self.name if c.isalpha()).upper()
            prefix = alpha_chars[:3] if len(alpha_chars) >= 3 else (alpha_chars or 'CAT')
            # Pad prefix to 3 chars if name is very short (e.g. "AI" -> "AI" stays "AI")
            # But spec says "first 3 letters", so 1-2 letter names keep their short prefix
            # To keep it simple and consistent, pad with 'X' if less than 3:
            prefix = prefix.ljust(3, 'X')[:3]

            # 2. Find the next sequential number for this prefix
            existing_codes = Category.objects.filter(
                organization=self.organization,
                code__startswith=prefix
            ).values_list('code', flat=True)

            max_num = 0
            for code in existing_codes:
                # code is like "ITE001", "ITE002", etc.
                suffix = code[len(prefix):]
                try:
                    num = int(suffix)
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError):
                    continue

            next_num = max_num + 1
            self.code = f"{prefix}{next_num:03d}"

        super().save(*args, **kwargs)

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
    # Inefficient but safe way to find max number due to string sorting issues
    # "AST-00009" > "AST-00010" in string comparison
    assets = Asset.objects.filter(organization=organization, asset_tag__startswith='AST-').values_list('asset_tag', flat=True)
    
    max_num = 0
    for tag in assets:
        try:
            # tag is "AST-xxxxx"
            parts = tag.split('-')
            if len(parts) > 1:
                num = int(parts[1])
                if num > max_num:
                    max_num = num
        except (ValueError, IndexError):
            continue
            
    new_number = max_num + 1
    return f"AST-{new_number:05d}"

class Asset(TenantAwareModel):
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
    useful_life_years = models.PositiveIntegerField(default=5, blank=True, null=True)
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

    expected_units = models.PositiveBigIntegerField(null=True, blank=True)
    units_consumed = models.PositiveBigIntegerField(default=0, blank=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_assets')

    @property
    def accumulated_depreciation(self):
        if not self.purchase_price or not self.purchase_date or not self.useful_life_years:
            return Decimal('0.00')
        
        years_passed = (date.today() - self.purchase_date).days / 365.25
        if years_passed <= 0:
            return Decimal('0.00')

        cost = float(self.purchase_price)
        salvage = float(self.salvage_value)
        life = float(self.useful_life_years)

        acc_dep = 0.0

        if self.depreciation_method == DepreciationMethod.STRAIGHT_LINE:
            # (Cost - Salvage) / Life * Years
            annual_dep = (cost - salvage) / life if life > 0 else 0
            acc_dep = annual_dep * years_passed
        
        elif self.depreciation_method == DepreciationMethod.DOUBLE_DECLINING:
            # Rate = 2 / Life
            # This is complex to calc for partial years without a loop, usually done per year.
            # Using approximation or iterative approach for accurate NBV?
            # For property display, let's just do a quick approx or simple loop.
            rate = 2.0 / life if life > 0 else 0
            current_val = cost
            # Integer years loop
            full_years = int(years_passed)
            remainder = years_passed - full_years
            
            for _ in range(full_years):
                dep = current_val * rate
                current_val -= dep
            
            # Partial year
            dep = current_val * rate * remainder
            current_val -= dep
            
            acc_dep = cost - current_val

        elif self.depreciation_method == DepreciationMethod.UNITS_OF_PRODUCTION:
            if self.expected_units and self.expected_units > 0:
                rate_per_unit = (cost - salvage) / float(self.expected_units)
                acc_dep = rate_per_unit * float(self.units_consumed)
            else:
                acc_dep = 0.0

        elif self.depreciation_method == DepreciationMethod.SYD:
            # Sum of Years Digits
            # Denominator = n(n+1)/2
            n = int(life)
            denominator = n * (n + 1) / 2
            depreciable = cost - salvage
            
            # This is hard to calc "years_passed" continuously.
            # We'll just show 0 or implement detailed loop later if requested.
            # Simple approximation for now:
            acc_dep = 0.0 # Placeholder for complex SYD calc on property

        # Cap at depreciable amount
        depreciable_amount = cost - salvage
        if acc_dep > depreciable_amount:
            acc_dep = depreciable_amount
        
        return Decimal(str(acc_dep)).quantize(Decimal('0.01'))

    @property
    def current_value(self):
        if not self.purchase_price:
            return Decimal('0.00')
        val = self.purchase_price - self.accumulated_depreciation
        return val.quantize(Decimal('0.01'))

    def get_depreciation_schedule(self):
        if not self.purchase_price or not self.purchase_date or not self.useful_life_years:
            return []
            
        schedule = []
        cost = float(self.purchase_price)
        salvage = float(self.salvage_value)
        life = int(self.useful_life_years)
        if life < 1: life = 1
        
        current_nbv = cost
        acc_dep = 0.0
        
        for year_idx in range(1, life + 2): # +1 buffer
            year_date = self.purchase_date.year + year_idx - 1
            dep = 0.0

            if self.depreciation_method == DepreciationMethod.STRAIGHT_LINE:
                dep = (cost - salvage) / life
            
            elif self.depreciation_method == DepreciationMethod.DOUBLE_DECLINING:
                rate = 2.0 / life
                dep = current_nbv * rate
                
            elif self.depreciation_method == DepreciationMethod.SYD:
                # Year 1 (idx=1) -> Remaining Life = n
                # Year 2 (idx=2) -> Remaining Life = n-1
                denominator = life * (life + 1) / 2
                remaining_life = life - (year_idx - 1)
                if remaining_life > 0:
                    fraction = remaining_life / denominator
                    dep = (cost - salvage) * fraction
                else:
                    dep = 0.0

            # Last year adjustment or Cap
            if current_nbv - dep < salvage:
                dep = current_nbv - salvage
            
            if current_nbv <= salvage:
                dep = 0.0

            current_nbv -= dep
            acc_dep += dep
            
            schedule.append({
                'year': year_idx,
                'year_date': year_date,
                'depreciation': Decimal(str(dep)).quantize(Decimal('0.01')),
                'accumulated': Decimal(str(acc_dep)).quantize(Decimal('0.01')),
                'nbv': Decimal(str(current_nbv)).quantize(Decimal('0.01'))
            })

            if current_nbv <= salvage:
                break
                
        return schedule

    def save(self, *args, **kwargs):
        if self.category and self._state.adding:
            # inherit life/method/salvage/units
            if self.useful_life_years in (None, 0):
                self.useful_life_years = self.category.useful_life_years

            if not self.depreciation_method:
                self.depreciation_method = self.category.depreciation_method

            if self.salvage_value is None or self.salvage_value == 0:
                self.salvage_value = self.category.default_salvage_value

            if self.depreciation_method == DepreciationMethod.UNITS_OF_PRODUCTION:
                if not self.expected_units:
                    self.expected_units = self.category.default_expected_units

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
