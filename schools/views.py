from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import SchoolUser

@ login_required
def SchoolUserView(request):
    my_schools = SchoolUser.objects.filter(creator=request.user)