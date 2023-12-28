from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.db.models import Q
from schools.models import SchoolUser, Department
from reservations.models import ReservationPeriod, Reservation, ReservationWindow, SchoolYear
from schools.forms import SchoolUserForm
from .forms import SchoolUserUpdateForm
from datetime import datetime
import pytz

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
        'school_users_num': len(school_users),
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

@login_required
@user_passes_test(lambda u: u.is_superuser)
def schools_created_by_admin(request):

    superuser_school_users = SchoolUser.objects.filter(creator__is_superuser=True).order_by('school__name')

    context = {
        'superuser_school_users': superuser_school_users,
        'superuser_school_users_num': len(superuser_school_users),
    }

    return render(request, 'schoolsadmin/schools_created_by_admin.html', context)

@ login_required
@user_passes_test(lambda u: u.is_superuser)
def SchoolUserUpdateView(request, school_id):
    school_update = get_object_or_404(SchoolUser, id=school_id) 
    schoolUpdateForm = SchoolUserUpdateForm(instance=school_update)

    if request.method == 'POST':
        schoolUpdateForm = SchoolUserUpdateForm(request.POST, instance=school_update)
        if schoolUpdateForm.is_valid():
            schoolUpdateForm.save()
            return redirect(reverse('schoolsadmin:schools_created_by_admin'))

    return render(request, 'schoolsadmin/school_update_admin.html', {'school_update':school_update, 'schoolUpdateForm': schoolUpdateForm,})

@ login_required
@user_passes_test(lambda u: u.is_superuser)
def SchoolUserDeleteView(request, school_id):
    school_delete = get_object_or_404(SchoolUser, id=school_id) 

    if request.method == 'POST':         
        school_delete.delete()                    
        return redirect('schoolsadmin:schools_created_by_admin')           

    return render(request, 'schoolsadmin/school_delete_admin.html', {'school_delete': school_delete})

@ login_required
@user_passes_test(lambda u: u.is_superuser)
def school_reservations_admin(request, school_id):

    # Get current UTC time
    utc_now = datetime.now(pytz.utc)

    # Define the Athens time zone
    athens_tz = pytz.timezone('Europe/Athens')

    # Convert UTC time to Athens time
    athens_now = utc_now.astimezone(athens_tz)

    #query user's reservations
    my_reservations = Reservation.objects.filter(schoolUser=school_id).order_by('-reservation_date__date', 'timeslot__dayTime__slot')

    #query current school year
    current_school_year = SchoolYear.objects.filter(start_date__lte=athens_now, end_date__gte=athens_now).first()
    if current_school_year:   
        # Use Q objects to handle the OR condition for start and end dates
        query = Q(schoolUser=school_id) & Q(reservation_period__schoolYear=current_school_year)
        # Filter reservations based on the current school year and the user
        my_reservations_current_year_number = len(Reservation.objects.filter(query).exclude(status='denied'))
    else:
        my_reservations_current_year_number = 0


    #query closest available reservation period whose start date hasn't come yet and res window has not finished yet - closest_available_res_period[0]
    q = ReservationPeriod.objects.filter(is_available=True).filter(start_date__gte=athens_now).filter(reservationwindow__end_date__gte=athens_now)
    
    #ensure that admin has made a ReservationPeriod available
    if len(q) > 0:
    
        dates = q.values('start_date').order_by('start_date')
        closest_available_res_period = q.filter(start_date=dates[0]['start_date'])

        try:
            #ensure that user has created a school
            my_school = get_object_or_404(SchoolUser, id=school_id) 

            #ensure that admin has created a ReservationWindow
            if len(ReservationWindow.objects.filter(reservation_period=closest_available_res_period[0])) > 0:

                context = {'my_reservations': my_reservations,
                        'my_reservations_current_year_number': my_reservations_current_year_number,
                        'next_available_res_period': closest_available_res_period[0],
                        'next_available_res_period_start_date': closest_available_res_period[0].start_date,
                        'next_available_res_period_end_date': closest_available_res_period[0].end_date,
                        'reservation_allowed': closest_available_res_period[0].reservationwindow_set.first().is_reservation_allowed(),
                        'my_school': my_school,
                }

                # need to check if the res period of the already registered user's reservations is the same with the next available res period
                if my_reservations:
                    context = {'my_reservations': my_reservations,
                            'my_reservations_current_year_number': my_reservations_current_year_number,
                            'my_reservation_period': ReservationPeriod.objects.filter(reservation__schoolUser__creator=request.user).first(),
                            'next_available_res_period': closest_available_res_period[0],
                            'next_available_res_period_start_date': closest_available_res_period[0].start_date,
                            'next_available_res_period_end_date': closest_available_res_period[0].end_date,
                            'reservation_allowed': closest_available_res_period[0].reservationwindow_set.first().is_reservation_allowed(),
                            'my_school': my_school,
                        }

                return render(request, 'schoolsadmin/school_reservations_admin.html', context)

            else:

                context = {'my_reservations': my_reservations,
                        'my_reservations_current_year_number': my_reservations_current_year_number,
                        'my_school': my_school,
                }

                return render(request, 'schoolsadmin/school_reservations_admin.html', context)               

        except (IndexError, SchoolUser.DoesNotExist):
            return render(request, 'schoolsadmin/school_reservations_admin.html')

    else:

        try:
            my_school = get_object_or_404(SchoolUser, id=school_id) 

            context = {'my_reservations': my_reservations,
                    'my_reservations_current_year_number': my_reservations_current_year_number,
                    'my_school': my_school,
            }

            return render(request, 'schoolsadmin/school_reservations_admin.html', context)

        except (IndexError, SchoolUser.DoesNotExist):
            return render(request, 'schoolsadmin/school_reservations_admin.html')