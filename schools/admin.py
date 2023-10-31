from django.contrib import admin
from .models import Department, School, SchoolUser
# Register your models here.

admin.site.register(Department)
admin.site.register(School)
admin.site.register(SchoolUser)