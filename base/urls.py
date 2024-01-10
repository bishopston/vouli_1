from django.urls import path
from .views import HomePageView, AdminDashboardView, UserDashboardView, SchoolSearchView, SchoolSearchAutoCompleteView, AccountEditView

app_name = 'base'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('admin_dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('user_dashboard/', UserDashboardView.as_view(), name='user_dashboard'),
    path('searchschool/', SchoolSearchView, name='school_search'),
    path('searchschoolautocomplete/', SchoolSearchAutoCompleteView, name='school_search_autocomplete'),
    path('account_edit/', AccountEditView, name='account_edit')
]