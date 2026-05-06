from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from apps.core.views import DashboardView
from apps.users.views import SignUpView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
    path('signup/', SignUpView.as_view(), name='signup'),
    
    # Web URLs
    path('assets/', include('apps.assets.urls')),
    path('locations/', include('apps.locations.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('users/', include('apps.users.urls')),
    
    # API URLs
    path('api/', include('apps.api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Serve user-uploaded media (QR codes, barcodes, asset images, etc.) in
    # production when files live on a persistent volume rather than cloud
    # storage. Skip this branch when MEDIA_URL points at an external CDN/bucket
    # (configured via AWS_* env vars in settings.py).
    if settings.MEDIA_URL.startswith('/'):
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
