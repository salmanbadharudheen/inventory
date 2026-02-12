
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import RequestFactory
from apps.assets.views import CategoryCreateView
from apps.assets.forms import CategoryForm
from apps.assets.models import Category

def test_category_form():
    print("Testing CategoryForm instantiation...")
    try:
        form = CategoryForm()
        print("Form fields:", form.fields.keys())
        print("Form instantiated successfully.")
        
        print("Testing Form Rendering...")
        rendered = form.as_p()
        print("Form rendered successfully (simulated).")
        
    except Exception as e:
        print("FAILED to instantiate/render form:", e)
        import traceback
        traceback.print_exc()

def test_view_execution():
    print("\nTesting CategoryCreateView GET request...")
    request = RequestFactory().get('/assets/categories/add/')
    # Mock user
    from django.contrib.auth import get_user_model
    User = get_user_model()
    try:
        user = User.objects.first()
        if not user:
            print("No user found to mock login.")
            return
        request.user = user
        
        view = CategoryCreateView.as_view()
        response = view(request)
        print("View response status:", response.status_code)
        
        if hasattr(response, 'render'):
            print("Rendering response...")
            response.render()
            print("Render successful.")
            
        print("Content:", response.content.decode('utf-8')[:500])
             
    except Exception as e:
        print("FAILED to execute view:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_category_form()
    test_view_execution()
