from django.db import models
from django.conf import settings

class Department(models.Model):
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name

class School(models.Model):
    name = models.CharField(max_length=300)
    periphery = models.CharField(max_length=300, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    ota_municipality = models.CharField(max_length=50, blank=True)
    education_level = models.CharField(max_length=50, blank=True)
    type = models.CharField(max_length=150, blank=True)
    legal_character = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.name

class SchoolUser(models.Model):
    creator = models.ForeignKey(
	    settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, default=None)
    director_name = models.CharField(max_length=30)
    director_surname = models.CharField(max_length=50)
    address = models.CharField(max_length=50)
    address_number = models.IntegerField()
    city = models.CharField(max_length=50)
    zipcode = models.IntegerField()
    phone = models.IntegerField()
    privacy_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.school.name