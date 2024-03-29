"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from .views import custom_login_redirect#, delete_account

urlpatterns = [
    path("admin/", admin.site.urls),

    # User management
    path('custom_login_redirect/', custom_login_redirect, name='custom_login_redirect'),
    #path('delete_account', delete_account, name='delete_account'),
    #path('accounts/login/', CustomLoginView.as_view(), name='account_login'),
    path('accounts/', include('allauth.urls')),

    # Local apps
    path('', include('base.urls')),
    path('schools/', include('schools.urls')),
    path('reservations/', include('reservations.urls')),   
    path('schoolsadmin/', include('schoolsadmin.urls')),
]
