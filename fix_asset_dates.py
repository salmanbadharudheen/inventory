#!/usr/bin/env python
"""
Script to fix assets with missing purchase dates.
Sets purchase_date to today's date for all assets without a purchase date.
"""
import os
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.assets.models import Asset

# Find all assets without purchase_date
assets_no_date = Asset.objects.filter(purchase_date__isnull=True)
count = assets_no_date.count()

print(f"Found {count} assets without purchase_date")

if count > 0:
    # Update all of them with today's date
    today = date.today()
    print(f"Setting purchase_date to {today} for all {count} assets...")
    
    updated = assets_no_date.update(purchase_date=today)
    
    print(f"✓ Successfully updated {updated} assets with purchase_date={today}")
    
    # Verify
    remaining = Asset.objects.filter(purchase_date__isnull=True).count()
    print(f"Remaining assets without purchase_date: {remaining}")
else:
    print("✓ All assets have a purchase_date!")
