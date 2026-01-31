import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.core.models import Organization
from apps.users.models import User
from apps.locations.models import Branch, Department

def init_data():
    # 1. Create Organization
    org, created = Organization.objects.get_or_create(
        name="TechCorp HQ",
        defaults={'slug': 'techcorp-hq'}
    )
    if created:
        print(f"Created Org: {org}")
    else:
        print(f"Found Org: {org}")

    # 2. Assign Superuser to Org
    admin = User.objects.get(username='admin')
    if not admin.organization:
        admin.organization = org
        admin.save()
        print(f"Assigned admin to {org}")

    # 3. Create Default Branch
    branch, created = Branch.objects.get_or_create(
        code="HQ-001",
        organization=org,
        defaults={'name': "Main Office", 'country': "USA"}
    )
    
    # 4. Create Default Department
    dept, created = Department.objects.get_or_create(
        name="IT Department",
        branch=branch,
        organization=org
    )

if __name__ == '__main__':
    init_data()
