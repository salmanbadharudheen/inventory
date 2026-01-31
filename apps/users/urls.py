from django.urls import path
from .views import AdminCreateView, UserListView

urlpatterns = [
    path('admins/add/', AdminCreateView.as_view(), name='admin-add'),
    path('', UserListView.as_view(), name='user-list'),
]
