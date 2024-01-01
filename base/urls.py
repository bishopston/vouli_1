from django.urls import path
from .views import HomePageView, AdminDashboardView, UserDashboardView

app_name = 'base'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('admin_dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('user_dashboard/', UserDashboardView.as_view(), name='user_dashboard'),
]