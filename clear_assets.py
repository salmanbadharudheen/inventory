#!/usr/bin/env python
"""
Script to safely delete all asset data from the database.
Only deletes Asset records, not related entities like Category, Brand, Department, etc.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.assets.models import Asset

def clear_assets():
    """Delete all asset records"""
    count = Asset.objects.count()
    
    if count == 0:
        print("✓ No assets to delete")
        return
    
    print(f"⚠️  Found {count} assets")
    confirm = input(f"Are you sure you want to delete all {count} assets? (yes/no): ")
    
    if confirm.lower() == 'yes':
        Asset.objects.all().delete()
        print(f"✓ Successfully deleted {count} assets")
        print("✓ All other data (categories, brands, departments, etc.) remains intact")
    else:
        print("✗ Deletion cancelled")

if __name__ == '__main__':
    clear_assets()
