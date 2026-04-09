"""
Load production data into the database if it's empty.
Usage: python manage.py load_initial_data
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command

User = get_user_model()

if User.objects.exists():
    print("Database already has data. Skipping fixture load.")
else:
    print("Empty database detected. Loading production data...")
    call_command('loaddata', 'fixtures/production_data.json')
    print("Done! Data loaded successfully.")
