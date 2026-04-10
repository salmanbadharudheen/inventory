from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    """No-op: AssetTransfer table is created by 0020_assettransfer instead."""

    dependencies = [
        ('locations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assets', '0018_approvalrequest_approvallog'),
    ]

    operations = [
        # Intentionally empty — 0020 creates AssetTransfer with all required fields.
    ]
