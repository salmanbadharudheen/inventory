import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import Organization
from apps.locations.models import Branch, Department

def bulk_add_departments():
    org = Organization.objects.get(name="TechCorp HQ")
    branch = Branch.objects.get(organization=org, code="MAIN")
    
    departments = [
        'BEACH',
        'CAFETERIA',
        'ENGINEERING',
        'F&B',
        'GENERAL WORKSHOP',
        'HOUSEKEEPING'
    ]
    
    created_count = 0
    skipped_count = 0

    for dept_name in departments:
        name = dept_name.strip().title()
        dept, created = Department.objects.get_or_create(
            organization=org,
            branch=branch,
            name=name
        )
        if created:
            created_count += 1
        else:
            skipped_count += 1

    print(f"Successfully added {created_count} departments.")
    print(f"Skipped {skipped_count} existing departments.")

if __name__ == '__main__':
    bulk_add_departments()
