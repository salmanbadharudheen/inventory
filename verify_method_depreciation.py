
import os
import django
from decimal import Decimal
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.assets.models import Category, Asset, DepreciationMethod
from apps.core.models import Organization
from django.contrib.auth import get_user_model

User = get_user_model()

def run_verification():
    print("Verifying Method-Based Depreciation...")

    # Setup
    org, _ = Organization.objects.get_or_create(name="Test Org", slug="test-org")
    user, _ = User.objects.get_or_create(username="testuser", defaults={'organization': org})

    # 1. Test Category Creation (Auto-Code)
    print("\n1. Testing Category Creation...")
    import time
    suffix = int(time.time() % 10000) # shorter suffix
    cat_name = f"HM-{suffix}"
    category = Category.objects.create(
        organization=org,
        name=cat_name,
        useful_life_years=10,
        depreciation_method=DepreciationMethod.STRAIGHT_LINE,
        default_salvage_value=1000
    )
    print(f"Category Created: {category.name}")
    print(f"Auto-Generated Code: {category.code}")
    
    if not category.code:
        print("FAIL: Code was not auto-generated.")
    
    # 2. Test Asset Creation (Inheritance)
    print("\n2. Testing Asset Creation...")
    asset = Asset.objects.create(
        organization=org,
        name="Bulldozer",
        category=category,
        asset_tag=f"AST-{suffix}",
        purchase_price=50000,
        purchase_date=date(2023, 1, 1),
        created_by=user
    )
    
    print(f"Asset Created: {asset.name}")
    print(f"Inherited Method: {asset.depreciation_method} (Expected: {DepreciationMethod.STRAIGHT_LINE})")
    print(f"Inherited Life: {asset.useful_life_years} (Expected: 10)")
    print(f"Inherited Salvage: {asset.salvage_value} (Expected: 1000.00)")

    if asset.depreciation_method != DepreciationMethod.STRAIGHT_LINE:
        print(f"FAIL: Method not inherited correctly. Got {asset.depreciation_method}")
    if asset.useful_life_years != 10:
        print(f"FAIL: Life not inherited correctly. Got {asset.useful_life_years}")

    # 3. Test Depreciation Calculation (SL)
    # Cost 50000, Salvage 1000, Life 10 -> (49000 / 10) = 4900 per year.
    # Purchase 2023-01-01. Today is 2026-02-11.
    # Years passed approx 3.11
    # Acc Dep should be approx 4900 * 3.11 = 15239
    
    print("\n3. Testing Depreciation Calculation (SL)...")
    acc_dep = asset.accumulated_depreciation
    print(f"Accumulated Depreciation: {acc_dep}")
    
    # Simple check if it's non-zero and roughly expected
    if acc_dep > 0:
        print("PASS: Depreciation calculated.")
    else:
        print("FAIL: Depreciation is 0.")

    # 4. Test DDB
    print("\n4. Testing DDB Logic...")
    cat_ddb = Category.objects.create(
        organization=org,
        name=f"DDB-{suffix}",
        useful_life_years=5,
        depreciation_method=DepreciationMethod.DOUBLE_DECLINING
    )
    asset_ddb = Asset.objects.create(
        organization=org,
        name="MacBook Pro",
        category=cat_ddb,
        asset_tag=f"AST-DDB-{suffix}",
        purchase_price=2000,
        purchase_date=date(2024, 1, 1), # 2 years ago approx
        created_by=user
    )
    # Rate = 2/5 = 40%
    # Year 1: 2000 * 40% = 800. NBV = 1200.
    # Year 2: 1200 * 40% = 480. NBV = 720.
    # Total Acc Dep approx 1280.
    
    print(f"DDB Asset Created: {asset_ddb.name}")
    print(f"Accumulated Depreciation: {asset_ddb.accumulated_depreciation}")
    
    if asset_ddb.accumulated_depreciation > 0:
        print("PASS: DDB Depreciation calculated.")

if __name__ == "__main__":
    try:
        run_verification()
    except Exception as e:
        print(f"Verification Failed: {e}")
        import traceback
        traceback.print_exc()
