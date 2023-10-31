from django.urls import include, path

from . import views

urlpatterns = [
    #path('', views.SchoolUserView, name='schooluser_list'),
    path('add/', views.SchoolUserCreateView, name='schooluser_add'),
    #path('<int:pk>/', views.SchoolUserUpdateView, name='schooluser_update'),
    path('ajax/load-schools/', views.load_schools, name='ajax_load_schools'),
]