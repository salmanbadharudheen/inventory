from django.db import migrations
from django.db.models import Count


def dedupe_departments(apps, schema_editor):
    Department = apps.get_model('locations', 'Department')
    db_alias = schema_editor.connection.alias

    duplicate_groups = (
        Department.objects.using(db_alias)
        .values('organization_id', 'branch_id', 'name')
        .annotate(total=Count('id'))
        .filter(total__gt=1)
    )

    for group in duplicate_groups:
        depts = list(
            Department.objects.using(db_alias)
            .filter(
                organization_id=group['organization_id'],
                branch_id=group['branch_id'],
                name=group['name'],
            )
            .order_by('id')
        )

        keeper = depts[0]
        duplicates = depts[1:]

        for duplicate in duplicates:
            for rel in Department._meta.related_objects:
                if rel.one_to_many or rel.one_to_one:
                    rel.related_model.objects.using(db_alias).filter(
                        **{rel.field.name: duplicate.pk}
                    ).update(**{rel.field.name: keeper.pk})
            duplicate.delete()


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ('locations', '0004_region_site_location_sublocation'),
    ]

    operations = [
        migrations.RunPython(dedupe_departments, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='department',
            unique_together={('organization', 'branch', 'name')},
        ),
    ]
