from django.contrib import admin
from django.urls import path, include
from apps.core.views import DashboardView
from apps.users.views import SignUpView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
    path('signup/', SignUpView.as_view(), name='signup'),
    path('assets/', include('apps.assets.urls')),
    path('locations/', include('apps.locations.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('users/', include('apps.users.urls')),
]
