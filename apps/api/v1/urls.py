from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'api_v1'

urlpatterns = [
    # Root
    path('', views.api_root, name='api-root'),
    
    # Authentication endpoints
    path('auth/login/', views.LoginAPIView.as_view(), name='login'),
    path('auth/logout/', views.LogoutAPIView.as_view(), name='logout'),
    path('auth/register/', views.RegisterAPIView.as_view(), name='register'),
    path('auth/profile/', views.UserProfileAPIView.as_view(), name='profile'),
    path('auth/change-password/', views.ChangePasswordAPIView.as_view(), name='change-password'),
    
    # JWT Token endpoints
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
