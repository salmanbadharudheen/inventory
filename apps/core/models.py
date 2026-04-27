from django.db import models
import uuid

class Organization(models.Model):
    class TagSegment(models.TextChoices):
        COMPANY = 'COMPANY', 'Company Code (first 2 letters)'
        CATEGORY = 'CATEGORY', 'Category Code (3 letters)'
        SEQUENCE = 'SEQUENCE', 'Sequential Number'
        YEAR = 'YEAR', 'Year Suffix (2 digits)'

    class SequenceFormat(models.TextChoices):
        HEX4 = 'HEX4', '4-Digit Hex (001A)'
        HEX6 = 'HEX6', '6-Digit Hex (00001A)'
        NUM4 = 'NUM4', '4-Digit Number (0001)'
        NUM5 = 'NUM5', '5-Digit Number (00001)'
        NUM6 = 'NUM6', '6-Digit Number (000001)'

    class LabelTemplate(models.TextChoices):
        CLASSIC = 'CLASSIC', 'Classic – QR left, Barcode right'
        COMPACT = 'COMPACT', 'Compact – QR + Tag only (small sticker)'
        DETAILED = 'DETAILED', 'Detailed – QR, Barcode, Name, Category, Location'
        BARCODE_ONLY = 'BARCODE_ONLY', 'Barcode Only – Horizontal barcode strip'
        MODERN = 'MODERN', 'Modern – Gradient header, Name, Category, Location'
        QR_ONLY = 'QR_ONLY', 'QR Only – Large QR code with tag'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Asset Tag Customization
    tag_prefix = models.CharField(
        max_length=20, blank=True,
        verbose_name="Fixed Tag Prefix",
        help_text="Optional fixed prefix for all asset tags (e.g. 'AST', 'INV'). Leave blank to use company code."
    )
    tag_separator = models.CharField(
        max_length=5, default='-',
        verbose_name="Separator",
        help_text="Character(s) between tag segments."
    )
    tag_include_company = models.BooleanField(
        default=True,
        verbose_name="Include Company Code",
        help_text="Include the 2-letter company code segment."
    )
    tag_include_category = models.BooleanField(
        default=True,
        verbose_name="Include Category Code",
        help_text="Include the 3-letter category code segment."
    )
    tag_include_year = models.BooleanField(
        default=True,
        verbose_name="Include Year Suffix",
        help_text="Append 2-digit year at the end."
    )
    tag_sequence_format = models.CharField(
        max_length=10,
        choices=SequenceFormat.choices,
        default=SequenceFormat.HEX4,
        verbose_name="Sequence Format",
        help_text="Number format for the sequential counter."
    )

    # Label / Sticker Design
    label_template = models.CharField(
        max_length=20,
        choices=LabelTemplate.choices,
        default=LabelTemplate.CLASSIC,
        verbose_name="Label Design",
        help_text="Default sticker label design used when printing asset labels."
    )

    def get_tag_preview(self):
        """Return a sample tag based on current settings."""
        sep = self.tag_separator or '-'
        parts = []
        if self.tag_prefix:
            parts.append(self.tag_prefix.upper())
        elif self.tag_include_company:
            parts.append('SH')
        if self.tag_include_category:
            parts.append('LAP')
        # Sequence
        fmt_map = {
            'HEX4': '001A', 'HEX6': '00001A',
            'NUM4': '0001', 'NUM5': '00001', 'NUM6': '000001',
        }
        parts.append(fmt_map.get(self.tag_sequence_format, '001A'))
        if self.tag_include_year:
            from datetime import date
            parts.append(str(date.today().year)[-2:])
        return sep.join(parts)

    def __str__(self):
        return self.name

class TenantAwareModel(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

