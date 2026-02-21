from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('assets', '0018_approvalrequest_approvallog'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetTransfer',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.organization')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('transfer_date', models.DateTimeField(auto_now_add=True)),
                ('expected_receipt_date', models.DateField(blank=True, null=True)),
                ('actual_receipt_date', models.DateField(blank=True, null=True)),
                ('transfer_reason', models.CharField(blank=True, help_text='Reason for transfer (e.g., Employee promotion, Department restructuring)', max_length=255)),
                ('notes', models.TextField(blank=True, help_text='Additional notes or comments')),
                ('received_comments', models.TextField(blank=True, help_text="Receiver's confirmation comments")),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('IN_TRANSIT', 'In Transit'), ('RECEIVED', 'Received'), ('REJECTED', 'Rejected'), ('CANCELLED', 'Cancelled')], default='PENDING', max_length=20)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='transfers', to='assets.asset')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transfers_initiated', to=settings.AUTH_USER_MODEL)),
                ('received_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transfers_received', to=settings.AUTH_USER_MODEL)),
                ('transferred_from_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assets_transferred_from', to=settings.AUTH_USER_MODEL)),
                ('transferred_to_user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assets_transferred_to', to=settings.AUTH_USER_MODEL)),
                ('transferred_from_department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assets_transferred_from', to='locations.department')),
                ('transferred_to_department', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assets_transferred_to', to='locations.department')),
                ('transferred_from_location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assets_transferred_from', to='locations.location')),
                ('transferred_to_location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assets_transferred_to', to='locations.location')),
            ],
            options={
                'verbose_name': 'Asset Transfer',
                'verbose_name_plural': 'Asset Transfers',
                'ordering': ['-created_at'],
            },
        ),
    ]
