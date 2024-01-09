from django.contrib import admin
from .models import Department, School, SchoolUser
# Register your models here.

admin.site.register(Department)

@admin.register(SchoolUser)
class SchoolUserAdmin(admin.ModelAdmin):
    list_display = ['school', 'department', 'creator']
    search_fields = ['school__name']
    list_filter = ['department']

@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ['name', 'department']
    search_fields = ['name']
    list_filter = ['department']