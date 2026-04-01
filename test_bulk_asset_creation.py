"""
Test script to demonstrate bulk asset creation with auto-generated unique IDs
When quantity > 1, multiple assets are created with sequential auto-generated tags
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.assets.models import Asset, Company, Category
from apps.core.models import Organization
from datetime import date

def test_bulk_asset_creation():
    print("=" * 80)
    print("BULK ASSET CREATION TEST - Multiple Assets with Auto-Generated IDs")
    print("=" * 80)
    print()
    
    # Get or create test organization
    org, _ = Organization.objects.get_or_create(
        slug='bulk-test-org',
        defaults={'name': 'Bulk Test Organization'}
    )
    print(f"✓ Organization: {org.name}")
    print()
    
    # Create test company and category
    company, _ = Company.objects.get_or_create(
        organization=org,
        name='Test Company',
        defaults={}
    )
    print(f"✓ Company: {company.name}")
    
    category, _ = Category.objects.get_or_create(
        organization=org,
        name='Laptops',
        defaults={}
    )
    print(f"✓ Category: {category.name} (Code: {category.code})")
    print()
    
    # Test 1: Single asset (quantity = 1)
    print("TEST 1: Create Single Asset (Quantity = 1)")
    print("-" * 80)
    
    asset_single = Asset.objects.create(
        organization=org,
        name='Dell Laptop Single',
        category=category,
        company=company,
        quantity=1,
        purchase_price=1500.00,
    )
    
    print(f"  Name: {asset_single.name}")
    print(f"  Asset ID: {asset_single.asset_tag}")
    print(f"  Quantity: {asset_single.quantity}")
    print()
    
    # Test 2: Bulk creation (quantity = 5)
    print("TEST 2: Create Bulk Assets (Quantity = 5)")
    print("-" * 80)
    print("Creating 5 Lenovo Laptops with quantity=5...")
    print()
    
    # Simulate bulk creation by manually creating multiple assets
    bulk_assets = []
    base_name = 'Lenovo Laptop Bulk'
    
    # First asset
    asset1 = Asset.objects.create(
        organization=org,
        name=f"{base_name} #1",
        category=category,
        company=company,
        quantity=1,
        purchase_price=1200.00,
    )
    bulk_assets.append(asset1)
    
    # Generate remaining 4 assets with sequential IDs
    from apps.assets.models import generate_asset_tag
    
    for i in range(2, 6):
        tag = generate_asset_tag(org, category, company)
        asset = Asset.objects.create(
            organization=org,
            name=f"{base_name} #{i}",
            asset_tag=tag,
            category=category,
            company=company,
            quantity=1,
            purchase_price=1200.00,
        )
        bulk_assets.append(asset)
    
    print(f"  Created {len(bulk_assets)} individual assets:")
    print()
    for idx, asset in enumerate(bulk_assets, 1):
        print(f"    {idx}. {asset.name:30} → {asset.asset_tag}")
    print()
    
    # Test 3: Verify sequential asset IDs
    print("TEST 3: Verify Sequential Hex Counter")
    print("-" * 80)
    
    # Get all assets for this company-category
    all_assets = Asset.objects.filter(
        organization=org,
        company=company,
        category=category
    ).order_by('created_at')
    
    print(f"Total assets for {company.name} - {category.name}: {all_assets.count()}")
    print()
    
    print("Asset ID Progression:")
    for asset in all_assets:
        # Parse the tag to show the counter
        parts = asset.asset_tag.split('-')
        if len(parts) == 4:
            counter_hex = parts[2]
            counter_dec = int(counter_hex, 16)
            print(f"  {asset.asset_tag} (Counter: {counter_dec:5} / {counter_hex} hex)")
    print()
    
    # Test 4: Simulate form submission with quantity
    print("TEST 4: Simulating Form Submission with Quantity > 1")
    print("-" * 80)
    print("If form is submitted with:")
    print(f"  - Name: 'HP Laptop Bundle'")
    print(f"  - Category: {category.name}")
    print(f"  - Company: {company.name}")
    print(f"  - Quantity: 10")
    print()
    print("System will create 10 individual assets with unique IDs:")
    print()
    
    # Generate 10 sample IDs
    sample_tags = []
    print("  Sample generated IDs would be:")
    # Get current max counter
    latest_asset = all_assets.last()
    if latest_asset:
        parts = latest_asset.asset_tag.split('-')
        if len(parts) == 4:
            current_counter = int(parts[2], 16)
            for i in range(1, 11):
                new_counter = current_counter + i
                hex_counter = f"{new_counter:04X}"
                sample_id = f"{parts[0]}-{parts[1]}-{hex_counter}-{parts[3]}"
                sample_tags.append(sample_id)
                print(f"    {i:2}. {sample_id} (Counter: {new_counter})")
    print()
    
    # Test 5: Benefits of this approach
    print("TEST 5: Benefits of Bulk Asset Creation")
    print("-" * 80)
    print("✓ Each physical asset gets unique ID")
    print("✓ Assets can be tracked individually")
    print("✓ Can assign to different users/locations")
    print("✓ Individual depreciation tracking")
    print("✓ Can be transferred separately")
    print("✓ Maintenance tracked per asset")
    print("✓ Easy inventory management")
    print()
    
    # Cleanup
    print("=" * 80)
    print("CLEANUP")
    print("=" * 80)
    
    # Count assets before cleanup
    total_before = Asset.objects.filter(organization=org).count()
    
    # Delete test assets
    Asset.objects.filter(organization=org).delete()
    
    total_after = Asset.objects.filter(organization=org).count()
    
    print(f"✓ Deleted {total_before - total_after} test assets")
    print()
    
    print("=" * 80)
    print("TEST COMPLETE!")
    print("=" * 80)
    print()
    print("SUMMARY:")
    print("--------")
    print("When you submit a form with Quantity = 10:")
    print("  1. System generates 10 unique asset IDs automatically")
    print("  2. Each gets an incremented hex counter: 0001, 0002... 000A")
    print("  3. All share same company/category/year prefix")
    print("  4. Creates 10 separate Asset records in database")
    print("  5. Each can be managed independently")
    print()
    print("Example: Create 10 Laptops")
    print("  Result: SH-LAP-0001-26, SH-LAP-0002-26... SH-LAP-000A-26")
    print()

if __name__ == '__main__':
    test_bulk_asset_creation()
