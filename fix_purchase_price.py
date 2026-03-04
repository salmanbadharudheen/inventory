#!/usr/bin/env python
"""
Script to fix misaligned purchase_price and currency data.
Some assets have numeric values in the 'currency' field that should be in 'purchase_price'.
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.assets.models import Asset
from decimal import Decimal

def fix_purchase_prices():
    """Fix assets where currency contains numeric values"""
    
    # Find all assets where currency looks like a price (numeric)
    all_assets = Asset.objects.all()
    fixed_count = 0
    
    for asset in all_assets:
        if asset.currency and asset.purchase_price is None:
            # Check if currency field contains a numeric value
            try:
                potential_price = Decimal(str(asset.currency))
                # If we got here, currency contains a number
                print(f"Fixing {asset.asset_tag}: Moving '{asset.currency}' from currency to purchase_price")
                asset.purchase_price = potential_price
                asset.currency = 'AED'  # Default to AED
                asset.save()
                fixed_count += 1
            except (ValueError, TypeError):
                # Currency is text (correct format)
                pass
    
    print(f"\n✓ Fixed {fixed_count} assets with misaligned purchase price data")
    
    # Summary
    assets_with_price = Asset.objects.filter(purchase_price__isnull=False).exclude(purchase_price=0).count()
    total_assets = Asset.objects.count()
    print(f"✓ Total assets with purchase price: {assets_with_price}/{total_assets}")

if __name__ == '__main__':
    fix_purchase_prices()
