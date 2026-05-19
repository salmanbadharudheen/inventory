from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0039_category_add_sub_group_fk'),
    ]

    operations = [
        migrations.AddField(
            model_name='assetdisposal',
            name='batch_reference',
            field=models.CharField(blank=True, db_index=True, max_length=36),
        ),
    ]
