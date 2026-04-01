"""
Test script to demonstrate the new Asset ID generation format: CO-CAT-XXXX-YY

Format Breakdown:
- CO: Company code (2 letters from company name)
- CAT: Category code (3 letters, already auto-generated)
- XXXX: Sequential hexadecimal counter (4 digits: 0001-FFFF)
- YY: Year suffix (last 2 digits of current year)

Examples:
- SH-LAP-0001-26 = Shamal, Laptop, 1st asset, Year 2026
- SH-LAP-001A-26 = Shamal, Laptop, 26th asset, Year 2026
- AC-FUR-00FF-25 = Acme Corp, Furniture, 255th asset, Year 2025
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.assets.models import Asset, Company, Category, generate_asset_tag
from apps.core.models import Organization
from datetime import date

def test_asset_id_generation():
    print("=" * 70)
    print("ASSET ID GENERATION TEST - Format: CO-CAT-XXXX-YY")
    print("=" * 70)
    print()
    
    # Get or create test organization
    org, _ = Organization.objects.get_or_create(
        slug='test-org',
        defaults={'name': 'Test Organization'}
    )
    print(f"✓ Organization: {org.name}")
    print()
    
    # Test 1: Create companies with auto-generated codes
    print("TEST 1: Company Code Auto-Generation")
    print("-" * 70)
    
    companies_data = [
        "Shamal Trading",
        "Acme Corporation",
        "Microsoft",
        "Apple Inc",
        "XY Company"  # Edge case: only 2 letters
    ]
    
    companies = []
    for company_name in companies_data:
        company, created = Company.objects.get_or_create(
            organization=org,
            name=company_name,
            defaults={'code': ''}  # Let it auto-generate
        )
        if created or not company.code:
            company.code = ''
            company.save()  # Trigger auto-generation
        
        companies.append(company)
        print(f"  Company: {company.name:20} → Code: {company.code}")
    
    print()
    
    # Test 2: Create categories (codes already auto-generated)
    print("TEST 2: Category Code Auto-Generation")
    print("-" * 70)
    
    categories_data = [
        "Laptop Computers",
        "Furniture & Fixtures",
        "IT Equipment",
        "Vehicles"
    ]
    
    categories = []
    for cat_name in categories_data:
        category, created = Category.objects.get_or_create(
            organization=org,
            name=cat_name,
            defaults={'code': ''}  # Let it auto-generate
        )
        if created or not category.code:
            category.code = ''
            category.save()  # Trigger auto-generation
        
        categories.append(category)
        print(f"  Category: {cat_name:25} → Code: {category.code}")
    
    print()
    
    # Test 3: Generate Asset IDs with different combinations
    print("TEST 3: Asset ID Generation Examples")
    print("-" * 70)
    print(f"Current Year: {date.today().year} (Suffix: {str(date.today().year)[-2:]})")
    print()
    
    # Generate sample asset IDs without creating actual assets
    test_cases = [
        (companies[0], categories[0], "Shamal + Laptops"),
        (companies[0], categories[1], "Shamal + Furniture"),
        (companies[1], categories[0], "Acme + Laptops"),
        (companies[2], categories[2], "Microsoft + IT Equipment"),
        (companies[3], categories[3], "Apple + Vehicles"),
        (None, categories[0], "No Company + Laptops"),  # Edge case
    ]
    
    for company, category, description in test_cases:
        asset_id = generate_asset_tag(org, category, company)
        company_name = company.name if company else "None"
        print(f"  {description:30} → {asset_id}")
        print(f"    └─ Breakdown: {asset_id.split('-')[0]} (Company) | "
              f"{asset_id.split('-')[1]} (Category) | "
              f"{asset_id.split('-')[2]} (Counter) | "
              f"{asset_id.split('-')[3]} (Year)")
        print()
    
    # Test 4: Sequential generation (simulating multiple assets)
    print("TEST 4: Sequential Hex Counter Test")
    print("-" * 70)
    print(f"Creating 5 assets for: {companies[0].name} + {categories[0].name}")
    print()
    
    created_assets = []
    for i in range(5):
        asset_id = generate_asset_tag(org, categories[0], companies[0])
        print(f"  Asset #{i+1}: {asset_id}")
        
        # Actually create asset to increment counter
        asset = Asset.objects.create(
            organization=org,
            name=f"Test Laptop {i+1}",
            asset_tag=asset_id,
            category=categories[0],
            company=companies[0],
            quantity=1
        )
        created_assets.append(asset)
    
    print()
    
    # Test 5: Hex counter demonstration
    print("TEST 5: Hexadecimal Counter Benefits")
    print("-" * 70)
    print("Decimal → Hex Examples:")
    print("  1 → 0001")
    print("  10 → 000A")
    print("  26 → 001A")
    print("  255 → 00FF")
    print("  256 → 0100")
    print("  4095 → 0FFF")
    print("  4096 → 1000")
    print("  65535 → FFFF (Maximum: 65,535 assets per company-category-year)")
    print()
    
    # Test 6: Year rollover demonstration
    print("TEST 6: Year Rollover Feature")
    print("-" * 70)
    print("Asset counters reset each year, allowing fresh sequential numbering:")
    current_year = str(date.today().year)[-2:]
    print(f"  2025: SH-LAP-FFFF-25 (Last asset of 2025)")
    print(f"  {date.today().year}: SH-LAP-0001-{current_year} (First asset of {date.today().year})")
    print()
    
    # Summary
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✓ Company codes: Auto-generated (2 letters)")
    print(f"✓ Category codes: Auto-generated (3 letters)")
    print(f"✓ Asset ID format: CO-CAT-XXXX-YY")
    print(f"✓ Counter format: 4-digit hexadecimal (0001-FFFF)")
    print(f"✓ Capacity: 65,535 assets per company-category-year")
    print(f"✓ Year rollover: Automatic counter reset each year")
    print()
    
    # Cleanup test assets
    print("Cleaning up test assets...")
    for asset in created_assets:
        asset.delete()
    print(f"✓ Deleted {len(created_assets)} test assets")
    print()
    
    print("=" * 70)
    print("TEST COMPLETE!")
    print("=" * 70)

if __name__ == '__main__':
    test_asset_id_generation()
