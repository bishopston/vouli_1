from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from schools.models import School, SchoolUser
from schools.forms import SchoolUserForm

@login_required
@user_passes_test(lambda u: u.is_superuser)
def school_selection(request):

    form = SchoolUserForm()
    context = {}

    department_id = request.GET.get('department')
    #school_id = request.GET.get('school')

    if request.GET.get('filter') == '1' and department_id:
        # Reset selected values
        form = SchoolUserForm()
        return redirect('schoolsadmin:schools_per_department', department_id=department_id)
    
    if request.GET.get('filter') == '1' and department_id is '':
        form = SchoolUserForm()
        return redirect('schoolsadmin:allschools')

    context.update({
        'form': form
    })

    return render(request, 'schoolsadmin/school_selection.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def all_schools(request):
    pass

@login_required
@user_passes_test(lambda u: u.is_superuser)
def schools_per_department(request, department_id):
    pass