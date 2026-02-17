import os
import django
from django.conf import settings
from django.template import loader
from django.test import RequestFactory
from django.contrib.auth import get_user_model

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

User = get_user_model()
factory = RequestFactory()

def test_dashboard_2row_layout():
    try:
        user = User.objects.filter(organization__isnull=False).first()
        if not user:
            user = User.objects.first()
            
        request = factory.get('/dashboard/')
        request.user = user
        
        from apps.core.views import DashboardView
        view = DashboardView.as_view()
        response = view(request)
        
        content = response.rendered_content
        
        # Check for new class names
        checks = [
            'mini-stat-card-elegant',
            'Geographic Infrastructure',
            'Asset Classification'
        ]
        
        all_passed = True
        for check in checks:
            if check in content:
                print(f"PASSED: Found '{check}'")
            else:
                print(f"FAILED: Could not find '{check}'")
                all_passed = False
        
        # Verify 2 rows exist
        grid_count = content.count('mini-stat-grid')
        if grid_count >= 2:
            print(f"PASSED: Found {grid_count} stat grids (2-row requirement met).")
        else:
            print(f"FAILED: Expected at least 2 stat grids, found {grid_count}.")
            all_passed = False

        if all_passed:
            print("\nAll 2-row layout checks PASSED!")
        else:
            print("\nSome 2-row layout checks FAILED.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dashboard_2row_layout()
