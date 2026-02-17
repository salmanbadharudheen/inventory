import os
import django
from django.test import RequestFactory
from django.template.loader import render_to_string
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.assets.models import Asset
from apps.assets.views import AssetDetailView

def test_detail_rendering():
    User = get_user_model()
    # Try to find a user and an asset
    user = User.objects.first()
    asset = Asset.objects.filter(organization=user.organization).first()
    
    if not asset:
        print("No asset found to test.")
        return

    print(f"Testing detail rendering for asset: {asset.name} ({asset.id})")
    
    factory = RequestFactory()
    request = factory.get(f'/assets/{asset.id}/')
    request.user = user
    
    view = AssetDetailView()
    view.request = request
    view.kwargs = {'pk': asset.id}
    view.object = asset
    
    context = view.get_context_data(object=asset)
    html = render_to_string(view.template_name, context, request=request)
    
    # Check for some key sections and fields
    checks = [
        ("General Identification", "Identification section missing"),
        ("Categorization", "Categorization section missing"),
        ("Location Hierarchy", "Location section missing"),
        ("Ownership & Assignment", "Ownership section missing"),
        ("Financial & Procurement", "Financial section missing"),
        ("Warranty, Maintenance & Insurance", "Warranty section missing"),
        ("Documents", "Documents section missing"),
        ("Notes & Remarks", "Notes section missing"),
        (asset.asset_tag, "Asset tag missing"),
        (asset.name, "Asset name missing"),
    ]
    
    all_passed = True
    for snippet, error_msg in checks:
        if snippet not in html:
            print(f"FAILED: {error_msg}")
            all_passed = False
        else:
            print(f"PASSED: Found '{snippet}'")
            
    if all_passed:
        print("\nAll rendering checks PASSED!")
    else:
        print("\nSome rendering checks FAILED.")

if __name__ == "__main__":
    try:
        test_detail_rendering()
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()
