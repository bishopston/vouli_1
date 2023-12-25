from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from schools.models import School, SchoolUser, Department
from schools.forms import SchoolUserForm

@login_required
@user_passes_test(lambda u: u.is_superuser)
def school_selection(request):

    form = SchoolUserForm()
    context = {}

    department_id = request.GET.get('department')
    #school_id = request.GET.get('school')

    if request.GET.get('filter') == '1' and department_id:
        print(department_id)
        print(request.GET.get('filter'))
        # Reset selected values
        form = SchoolUserForm()
        return redirect('schoolsadmin:schools_per_department', department_id=department_id)
    
    if request.GET.get('filter') == '1' and department_id is '':
        form = SchoolUserForm()
        return redirect('schoolsadmin:all_schools')

    context.update({
        'form': form
    })

    return render(request, 'schoolsadmin/school_selection.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def all_schools(request):

    school_users = SchoolUser.objects.all().order_by('school__name')

    context = {
        'school_users': school_users,
    }

    return render(request, 'schoolsadmin/all_schools.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def schools_per_department(request, department_id):
    
    dept = get_object_or_404(Department, id=department_id)
    school_users = SchoolUser.objects.filter(department=dept).order_by('department__name', 'school__name')

    context = {
        'dept': dept,
        'school_users': school_users,
    }

    return render(request, 'schoolsadmin/schools_per_department.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def schools_details(request, school_id):
    
    school_user = SchoolUser.objects.get(id=school_id)

    context = {
        'school_user': school_user,
    }

    return render(request, 'schoolsadmin/schools_details.html', context)