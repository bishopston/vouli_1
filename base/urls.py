from django.urls import path
from .views import HomePageView, AdminDashboardView

app_name = 'base'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('admin_dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
]