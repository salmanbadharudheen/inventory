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
    """Delete all asset records in batches to avoid SQLite variable limit"""
    count = Asset.objects.count()
    
    if count == 0:
        print("✓ No assets to delete")
        return
    
    print(f"⚠️  Found {count} assets")
    confirm = input(f"Are you sure you want to delete all {count} assets? (yes/no): ")
    
    if confirm.lower() == 'yes':
        # Delete in batches of 500 to avoid SQLite "too many SQL variables" error
        batch_size = 500
        deleted_total = 0
        
        while True:
            # Get next batch of asset IDs
            batch_ids = list(Asset.objects.values_list('id', flat=True)[:batch_size])
            
            if not batch_ids:
                break
            
            # Delete this batch
            deleted, _ = Asset.objects.filter(id__in=batch_ids).delete()
            deleted_total += deleted
            print(f"  Deleted {deleted_total}/{count} assets...")
        
        print(f"✓ Successfully deleted {deleted_total} assets")
        print("✓ All other data (categories, brands, departments, etc.) remains intact")
    else:
        print("✗ Deletion cancelled")

if __name__ == '__main__':
    clear_assets()
