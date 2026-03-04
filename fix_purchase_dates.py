#!/usr/bin/env python
"""
Script to fix missing purchase_date for all assets.
Uses date_placed_in_service if available, otherwise uses today's date.
"""

import os
import django
from datetime import date, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.assets.models import Asset

def fix_purchase_dates():
    """Fix assets with missing purchase_date"""
    
    total_assets = Asset.objects.count()
    fixed_count = 0
    
    for asset in Asset.objects.all():
        if asset.purchase_date is None:
            # Try to use date_placed_in_service, otherwise use today
            if asset.date_placed_in_service:
                asset.purchase_date = asset.date_placed_in_service
            else:
                # Set to 1 year ago from today for depreciation calculation
                asset.purchase_date = date.today() - timedelta(days=365)
            
            asset.save()
            fixed_count += 1
            
            if fixed_count % 1000 == 0:
                print(f"  Fixed {fixed_count}/{total_assets} assets...")
    
    print(f"\n✓ Fixed {fixed_count}/{total_assets} assets with missing purchase_date")
    
    # Show some examples
    print("\nSample assets with fixed dates:")
    for asset in Asset.objects.all()[:5]:
        print(f"  {asset.asset_tag}: {asset.name} - Date: {asset.purchase_date} - Depreciation: {asset.accumulated_depreciation}")

if __name__ == '__main__':
    fix_purchase_dates()
