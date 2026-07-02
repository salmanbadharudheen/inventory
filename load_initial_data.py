"""
Load initial fixture data into the database when explicitly enabled.
Usage: python manage.py load_initial_data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()

load_initial_data = os.environ.get('LOAD_INITIAL_DATA', 'False') == 'True'

if not load_initial_data:
    print("LOAD_INITIAL_DATA is not enabled. Skipping fixture load.")
elif User.objects.exists():
    print("Database already has data. Skipping fixture load.")
else:
    print("Empty database detected and LOAD_INITIAL_DATA is enabled. Loading fixture data...")
    call_command('loaddata', 'fixtures/production_data.json')
    print("Done! Data loaded successfully.")
