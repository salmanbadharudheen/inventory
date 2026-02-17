import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inventory.settings')
django.setup()

from apps.core.models import Organization

orgs = Organization.objects.all()
if not orgs:
    print("No organizations found.")
else:
    for org in orgs:
        print(f"ID: {org.id} | Name: {org.name}")
