from django.urls import include, path

from . import views

app_name = 'schools'

urlpatterns = [
    path('', views.SchoolUserView, name='schooluser_list'),
    path('add/', views.SchoolUserCreateView, name='schooluser_add'),
    path('delete/<int:school_id>', views.SchoolUserDeleteView, name='schooluser_delete'),
    #path('<int:pk>/', views.SchoolUserUpdateView, name='schooluser_update'),
    path('ajax/load-schools/', views.load_schools, name='ajax_load_schools'),
]