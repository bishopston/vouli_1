from django.urls import include, path

from . import views

app_name = 'schoolsadmin'

urlpatterns = [
    path('school_selection/', views.school_selection, name='school_selection'),
    path('all_schools/', views.all_schools, name='all_schools'),
    path('schools_per_department/<int:department_id>/', views.schools_per_department, name='schools_per_department'),
    path('schools_details/<int:school_id>/', views.schools_details, name='schools_details'),
    path('schools_created_by_admin/', views.schools_created_by_admin, name='schools_created_by_admin'),
    # path('add/', views.SchoolUserCreateView, name='schooluser_add'),
    path('delete/<int:school_id>/', views.SchoolUserDeleteView, name='schooluser_delete'),
    path('update/<int:school_id>/', views.SchoolUserUpdateView, name='schooluser_update'),
    # path('ajax/load-schools/', views.load_schools, name='ajax_load_schools'),
]