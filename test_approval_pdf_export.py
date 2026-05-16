import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.core.models import Organization

User = get_user_model()

# Get the superuser
try:
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        print('No superuser found')
        exit(1)
    
    # Check if user has an organization, create one if not
    print(f'User: {user.username}')
    print(f'Is superuser: {user.is_superuser}')
    print(f'Organization before: {user.organization}')
    
    # Create a default organization if none exist
    if not user.organization:
        org, created = Organization.objects.get_or_create(
            name='Default Organization',
            defaults={'slug': 'default-organization', 'is_active': True}
        )
        user.organization = org
        user.save()
        print(f'Organization assigned: {user.organization}')
    
    client = Client()
    client.force_login(user)
    
    # Set the session flag to enable org_mode for superuser
    session = client.session
    session['superuser_org_mode'] = True
    session.save()
    
    # Test the export URL without following redirects
    export_url = reverse('approval-request-export-pdf')
    print(f'\nTesting export URL: {export_url}')
    export_response = client.get(export_url, follow=False)
    
    print(f'Export Status Code: {export_response.status_code}')
    print(f'Content-Type: {export_response.get("Content-Type")}')
    print(f'Content-Disposition: {export_response.get("Content-Disposition")}')
    
    if export_response.status_code == 302:
        print(f'Redirect location: {export_response.get("Location")}')
    elif export_response.status_code == 200:
        print(f'Content Length: {len(export_response.content)}')
        if export_response.get("Content-Type") == 'application/pdf':
            print('\nAPPROVAL_PDF_STATUS=200')
            print('CONTENT_TYPE=application/pdf')
        else:
            print(f'\nWARNING: Got 200 but content-type is {export_response.get("Content-Type")}')
    else:
        print(f'Unexpected status: {export_response.status_code}')
        print(f'Response content: {export_response.content[:200]}')
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
