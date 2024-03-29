from django.shortcuts import render, redirect, HttpResponseRedirect, get_object_or_404
from django.http import Http404, HttpResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.forms import formset_factory
from django.core.serializers import serialize
from django.http import JsonResponse
from django.db.models import Q, Sum, IntegerField, F, Value, Count, Case, When
from django.db.models.functions import Cast
from django.db import transaction
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string, get_template
from django.views import View
from django.core.mail import EmailMessage
from .models import Day, ReservationPeriod, Timeslot, DayTime, Reservation, ReservationWindow, ExceptionalRule, SchoolYear
from schools.models import SchoolUser, Department
from .forms import ReservationForm, BaseReservationFormSet, ReservationUpdateForm, ReservationUpdateAdminForm, ReservationDashboardForm, ReservationCalendarByDateForm
from .utils import get_athens_now_time, get_occupied_daytimes, get_allowed_daytimes, get_occupied_exceptional_daytimes, get_allowed_exceptional_daytimes, calculate_availability_percentage
from datetime import timedelta
import datetime
from datetime import datetime as dt
import pytz
from datetime import datetime, date
from itertools import groupby
from xhtml2pdf import pisa
import base64



@ login_required
@user_passes_test(lambda u: u.is_superuser)   
def timeslot_res_period_selection(request):

    form = ReservationCalendarByDateForm()
    context = {}

    selected_reservation_period_id = request.GET.get('reservation_period')

    # Check if the Filter button is clicked
    if request.GET.get('filter') == '1' and selected_reservation_period_id:
        # Reset selected values
        form = ReservationCalendarByDateForm()
        timeslots = Timeslot.objects.filter(reservation_period=selected_reservation_period_id)
        # return redirect('reservations:edit_timeslots', reservation_period_id=selected_reservation_period_id)
    
        if timeslots:
            return redirect('reservations:edit_timeslots', reservation_period_id=selected_reservation_period_id)
        else:
            return redirect('reservations:add_timeslots', reservation_period_id=selected_reservation_period_id)
    
    if request.GET.get('filter') == '1' and selected_reservation_period_id == '':
        context['error_message'] = 'Πρέπει να διαλέξετε μία περίοδο επισκέψεων'

    if request.GET.get('filter') == '2':
        form = ReservationCalendarByDateForm()

    context.update({
        'form': form
    })

    return render(request, 'reservations/timeslots_res_period_selection.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_timeslots(request, reservation_period_id):

    qs_days = DayTime.objects.all().filter(slot='09:00:00').order_by('day').distinct()
    qs_slots = DayTime.objects.all().filter(day='a').order_by('slot').distinct()

    reservation_period = ReservationPeriod.objects.get(id=reservation_period_id)
    if request.method == 'POST':
        timeslots = request.POST.getlist('timeslots')

        for timeslot in timeslots:

            day, hour = timeslot.split()
            
            #print(f"Day: {day}, Hour: {hour}")
            submitted_timeslots = Timeslot.objects.filter(reservation_period=reservation_period, dayTime__day=day, dayTime__slot=hour)

            if submitted_timeslots.exists():
                return render(request, 'reservations/add_timeslots.html', {'reservation_period': reservation_period, 'qs_days': qs_days, 'qs_slots': qs_slots, 'error_message': 'Έχετε προβεί σε διπλοεγγραφή χρονοθυρίδας. Η ενέργεια ακυρώθηκε.'})

            else:
                # Create Timeslot objects based on the selected checkboxes
                Timeslot.objects.create(
                    reservation_period=reservation_period,
                    dayTime=DayTime.objects.get(day=day, slot=hour)
                )

        #return HttpResponseRedirect(request.path_info)
        return redirect(reverse('reservations:edit_timeslots' , kwargs={ 'reservation_period_id': reservation_period_id }))

    return render(request, 'reservations/add_timeslots.html', {'reservation_period': reservation_period, 'qs_days': qs_days, 'qs_slots': qs_slots})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_timeslots(request, reservation_period_id):
    reservation_period = ReservationPeriod.objects.get(id=reservation_period_id)
    timeslots = Timeslot.objects.filter(reservation_period=reservation_period).order_by('dayTime__day', 'dayTime__slot')
    
    if request.method == 'POST':
        selected_timeslots = request.POST.getlist('timeslots')
        
        # Update availability based on selected checkboxes
        for timeslot_id in selected_timeslots:
            timeslot = Timeslot.objects.get(id=timeslot_id)
            timeslot.is_reservation_allowed = not timeslot.is_reservation_allowed
            timeslot.save()
        
        return HttpResponseRedirect(request.path_info)

    return render(request, 'reservations/edit_timeslots_2.html', {'reservation_period': reservation_period, 'timeslots': timeslots})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_timeslots(request):
    if request.method == "POST":
        timeslot_ids = request.POST.getlist('id[]')
        for id in timeslot_ids:
            tslot = Timeslot.objects.get(pk=id)
            tslot.delete()
        return redirect(reverse('schools:schooluser_list'))
    

@ login_required
@user_passes_test(lambda u: u.is_superuser)   
def exceptional_rule_res_period_selection(request):

    form = ReservationCalendarByDateForm()
    context = {}

    selected_reservation_period_id = request.GET.get('reservation_period')

    # Check if the Filter button is clicked
    if request.GET.get('filter') == '1' and selected_reservation_period_id:
        # Reset selected values
        form = ReservationCalendarByDateForm()
        return redirect('reservations:calendar_timeslot', reservation_period_id=selected_reservation_period_id)
    
    if request.GET.get('filter') == '1' and selected_reservation_period_id == '':
        context['error_message'] = 'Πρέπει να διαλέξετε μία περίοδο επισκέψεων'

    if request.GET.get('filter') == '2':
        form = ReservationCalendarByDateForm()

    context.update({
        'form': form
    })

    return render(request, 'reservations/exceptional_rule_res_period_selection.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_exceptional_rule(request):

    # If the form was not submitted via POST, handle accordingly
    res_period_id = request.GET.get('reservationPeriodId') or request.POST.get('res_period_id')
    selected_date = request.GET.get('date') or request.POST.get('selected_date')
    error = request.GET.get('error', None)
    #print(error)

    day_of_week_mapping = {
        'Monday': 'a',
        'Tuesday': 'b',
        'Wednesday': 'c',
        'Thursday': 'd',
        'Friday': 'e',
        'Saturday': 'f',
        'Sunday': 'g',
    }
    #selected_day_of_week = day_of_week_mapping[Day.objects.get(date=selected_date).weekday()]
    selected_day = Day.objects.get(date=selected_date)
    #print(selected_day)
    selected_day_of_week = day_of_week_mapping[selected_day.date.strftime('%A')]
    #print(selected_day_of_week)

    # Find the corresponding DayTime instances for the determined day
    available_daytimes = DayTime.objects.filter(day=selected_day_of_week)
    #print(available_daytimes)

    created_exceptional_rules = ExceptionalRule.objects.filter(date=selected_day).order_by('timeslot')

    context = {}

    redirect_url = reverse('reservations:add_exceptional_rule')
    redirect_url += f'?date={selected_date}&reservationPeriodId={res_period_id}'

    if request.method == 'POST':
        #selected_date = request.POST.get('selected_date')
        #selected_date = request.GET.get('selected_date')
        selected_daytimes = request.POST.getlist('daytimes')
        #print(selected_date)

        # Check if the submitted daytimes already exist
        for daytime_id in selected_daytimes:
            #print(daytime_id)
            submitted_daytimes = ExceptionalRule.objects.filter(date=Day.objects.get(date=selected_date), timeslot=DayTime.objects.get(id=daytime_id))


            if submitted_daytimes.exists():
                #available_daytimes = DayTime.objects.filter(day=selected_day_of_week)
                error_message = 'Έχετε προβεί σε διπλοεγγραφή χρονοθυρίδας. Η ενέργεια ακυρώθηκε.'
                context['error_message'] = error_message
            
            # Create ExceptionalRule instances for the selected daytimes
            else:
                ExceptionalRule.objects.create(
                    date=Day.objects.get(date=selected_date),
                    timeslot=DayTime.objects.get(id=daytime_id),
                )
        context.update({
            'selected_date': selected_date, 
            'selected_day': selected_day, 
            'available_daytimes': available_daytimes,
            'created_exceptional_rules': created_exceptional_rules,
            'res_period_id': res_period_id,
        })

        # Redirect to a success page or any other page
        #return render(request, 'reservations/add_exceptional_rule.html', context)
        return redirect(redirect_url)

    context.update({
        'selected_date': selected_date, 
        'selected_day': selected_day, 
        'available_daytimes': available_daytimes,
        'created_exceptional_rules': created_exceptional_rules,
        'res_period_id': res_period_id,
        'error': error,
    })


    return render(request, 'reservations/add_exceptional_rule.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_exceptional_rule(request):

    res_period_id = request.GET.get('reservationPeriodId') or request.POST.get('res_period_id')
    selected_date = request.GET.get('date') or request.POST.get('selected_date')

    selected_day = Day.objects.get(date=selected_date)

    # created_exceptional_rules = ExceptionalRule.objects.filter(date=selected_day)

    redirect_url = reverse('reservations:add_exceptional_rule')
    redirect_url += f'?date={selected_date}&reservationPeriodId={res_period_id}'
    
    if request.method == 'POST':
        selected_timeslots = request.POST.getlist('timeslots')

        #print(len(ExceptionalRule.objects.filter(date=selected_day,is_reservation_allowed=True)))

        for timeslot_id in selected_timeslots:
            timeslot = ExceptionalRule.objects.get(id=timeslot_id)
            timeslot.is_reservation_allowed = not timeslot.is_reservation_allowed
            if len(ExceptionalRule.objects.filter(date=selected_day,is_reservation_allowed=True)) == 1:
                err_all_delete_message = 'Δεν μπορείτε να απενεργοποιήσετε όλες τις χρονοθυρίδες.'
                return redirect(redirect_url + f'&error={err_all_delete_message}')

            else:
                timeslot.save()
        
    #return HttpResponseRedirect(request.path_info)
    return redirect(redirect_url)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_exceptional_rule(request):

    res_period_id = request.GET.get('reservationPeriodId') or request.POST.get('res_period_id')
    selected_date = request.GET.get('date') or request.POST.get('selected_date')

    redirect_url = reverse('reservations:add_exceptional_rule')
    redirect_url += f'?date={selected_date}&reservationPeriodId={res_period_id}'

    if request.method == 'POST':
        selected_timeslots = request.POST.getlist('timeslots')
        
        # Update availability based on selected checkboxes
        for timeslot_id in selected_timeslots:
            timeslot = ExceptionalRule.objects.get(id=timeslot_id)
            timeslot.delete()
    
    return redirect(redirect_url)



@login_required
def calendar_month(request, reservation_period_id, school_user_id, year=None, month=None):

    # Get current UTC time
    utc_now = datetime.now(pytz.utc)

    # Define the Athens time zone
    athens_tz = pytz.timezone('Europe/Athens')

    # Convert UTC time to Athens time
    athens_now = utc_now.astimezone(athens_tz)

    # If reservation_period_id is provided, get the start date of the reservation period
    if reservation_period_id:
        #reservation_period = ReservationPeriod.objects.get(pk=reservation_period_id)
        reservation_period = get_object_or_404(ReservationPeriod, pk=reservation_period_id)
        school_user = get_object_or_404(SchoolUser, pk=school_user_id)
        if not year and not month:
            start_date = reservation_period.start_date
        else: 
            start_date = date(year, month, 1)
    else:
        # If no reservation_period_id is provided, use the current date
        start_date = athens_now

    # If year and month are not provided, use the start date
    if not year:
        year = start_date.year
    if not month:
        month = start_date.month

    # Calculate previous and next months
    prev_month = start_date - timedelta(days=start_date.day)
    next_month = start_date + timedelta(days=(32 - start_date.day))

    # Retrieve days for the current month
    month_days = get_month_days(year, month, reservation_period_id)

    for week in month_days:
        for day in week:
            if isinstance(day, Day):
                day.availability_percentage = calculate_availability_percentage(day.date, reservation_period_id)


    context = {
        #'current_month': f'{month}/{year}',
        'current_month': month,
        'current_year': year,
        'prev_year': prev_month.year,
        'prev_month': prev_month.month,
        'next_year': next_month.year,
        'next_month': next_month.month,
        'month_days': month_days,
        'reservation_period_id': reservation_period.id,
        'reservation_period': reservation_period,
        'reservation_period_allowed': reservation_period.reservationwindow_set.first().is_reservation_allowed(),
        'school_user': school_user,
    }

    if request.user.is_superuser:
        return render(request, 'reservations/calendar_month_admin.html', context)
    else:
        return render(request, 'reservations/calendar_month_user.html', context)

def get_month_days(year, month, res_period_id):
    # Assuming a Day model with a 'date' field
    res_period = ReservationPeriod.objects.get(pk=res_period_id)

    # Fetch the Day objects for the given month and year
    days = Day.objects.filter(
        Q(date__year=year, date__month=month) &
        Q(date__gte=res_period.start_date, date__lte=res_period.end_date)
    ).order_by('date')

    if not days:
        return []

    # Pad the beginning of the list with days from the previous week
    first_day_weekday = days[0].date.weekday()
    days = [days[0].date - timedelta(days=first_day_weekday)] * first_day_weekday + list(days)

    # Split the list into weeks
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]

    return weeks


def chunk_days(days):
    # Helper function to chunk days into weeks for rendering in the template
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]
    return weeks


@login_required
def my_reservations(request):

    # Get current UTC time
    utc_now = datetime.now(pytz.utc)

    # Define the Athens time zone
    athens_tz = pytz.timezone('Europe/Athens')

    # Convert UTC time to Athens time
    athens_now = utc_now.astimezone(athens_tz)

    #query user's reservations
    if not request.user.is_superuser:
        my_reservations = Reservation.objects.filter(schoolUser__creator=request.user).order_by('-reservation_date__date', 'timeslot__dayTime__slot', 'status')
    else:
        my_reservations = Reservation.objects.none()

    # need to check if the res period of the already registered user's reservations is the same with the next available res period
    # if my_reservations:
    #     my_reservation_period = ReservationPeriod.objects.filter(reservation__schoolUser__creator=request.user).first()

    #query current school year
    current_school_year = SchoolYear.objects.filter(start_date__lte=athens_now, end_date__gte=athens_now).first()
    if current_school_year:   
        # Use Q objects to handle the OR condition for start and end dates
        query = Q(schoolUser__creator=request.user) & Q(reservation_period__schoolYear=current_school_year)
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
            my_school = SchoolUser.objects.filter(creator=request.user)[0]#.school.name

            #ensure that admin has created a ReservationWindow
            if len(ReservationWindow.objects.filter(reservation_period=closest_available_res_period[0])) > 0:

                # need to check if the res period of the already registered user's reservations is the same with the next available res period
                if my_reservations:
                    #print(ReservationPeriod.objects.filter(reservation__schoolUser__creator=request.user).first().start_date)
                    context = {'my_reservations': my_reservations,
                            'my_reservations_current_year_number': my_reservations_current_year_number,
                            'my_reservation_period': ReservationPeriod.objects.filter(reservation__schoolUser__creator=request.user).first(),
                            'next_available_res_period': closest_available_res_period[0],
                            'next_available_res_period_start_date': closest_available_res_period[0].start_date,
                            'next_available_res_period_end_date': closest_available_res_period[0].end_date,
                            'reservation_allowed': closest_available_res_period[0].reservationwindow_set.first().is_reservation_allowed(),
                            'my_school': my_school,
                            'is_superuser': request.user.is_superuser,
                        }

                context = {'my_reservations': my_reservations,
                        'my_reservations_current_year_number': my_reservations_current_year_number,
                        'next_available_res_period': closest_available_res_period[0],
                        'next_available_res_period_start_date': closest_available_res_period[0].start_date,
                        'next_available_res_period_end_date': closest_available_res_period[0].end_date,
                        'reservation_allowed': closest_available_res_period[0].reservationwindow_set.first().is_reservation_allowed(),
                        'my_school': my_school,
                        'is_superuser': request.user.is_superuser,
                }

                return render(request, 'reservations/myreservations.html', context)

            else:

                context = {'my_reservations': my_reservations,
                        'my_reservations_current_year_number': my_reservations_current_year_number,
                        'my_school': my_school,
                        'is_superuser': request.user.is_superuser,
                }

                return render(request, 'reservations/myreservations.html', context)               

        except (IndexError, SchoolUser.DoesNotExist):
            return render(request, 'reservations/myreservations.html')

    else:

        try:
            my_school = SchoolUser.objects.filter(creator=request.user)[0]#.school.name

            context = {'my_reservations': my_reservations,
                    'my_reservations_current_year_number': my_reservations_current_year_number,
                    'my_school': my_school,
                    'is_superuser': request.user.is_superuser,
            }

            return render(request, 'reservations/myreservations.html', context)

        except (IndexError, SchoolUser.DoesNotExist):
            return render(request, 'reservations/myreservations.html')


@login_required
def make_reservation(request, reservation_period_id, school_user_id):

    # Get current UTC time
    utc_now = datetime.now(pytz.utc)

    # Define the Athens time zone
    athens_tz = pytz.timezone('Europe/Athens')

    # Convert UTC time to Athens time
    athens_now = utc_now.astimezone(athens_tz)

    schoolUser = SchoolUser.objects.get(pk=school_user_id)
    res_period = get_object_or_404(ReservationPeriod, pk=reservation_period_id)
    date = request.GET.get('date')
    preview_different_selected_date_violation_error = request.GET.get('preview_different_selected_date_violation_error', None)
    preview_max_allowed_violation_error = request.GET.get('preview_max_allowed_violation_error', None)

    #get week day name
    selected_date = datetime.strptime(date, "%Y-%m-%d")
    selected_calendar_date = Day.objects.get(date=selected_date)
    selected_calendar_date_name = selected_calendar_date.date.strftime("%A")

    #get date string
    #selected_calendar_date_string = selected_calendar_date.date.strftime("%d %B %Y")
    selected_calendar_date_day = selected_calendar_date.date.strftime("%d")
    selected_calendar_date_month = selected_calendar_date.date.strftime("%B")
    selected_calendar_date_year = selected_calendar_date.date.strftime("%Y")

    if len(ExceptionalRule.objects.filter(date = selected_calendar_date)) > 0:

        allowed_timeslots = get_allowed_exceptional_daytimes(date, reservation_period_id)
        occupied_timeslots = get_occupied_exceptional_daytimes(date, reservation_period_id)

    else:

        allowed_timeslots = get_allowed_daytimes(date, reservation_period_id)
        occupied_timeslots = get_occupied_daytimes(date, reservation_period_id)

    non_occupied_timeslots = allowed_timeslots.exclude(id__in=occupied_timeslots)
    non_occupied_timeslots_count = len(non_occupied_timeslots)

    context = {} 
    my_reservations = []
    
    ReservationFormSet = formset_factory(ReservationForm, extra=3, max_num=3, formset=BaseReservationFormSet)

    if request.method == 'POST':
        
        formset = ReservationFormSet(request.POST, reservation_period=res_period, selected_date=date)

        if request.POST.get('preview') == '1':

            if formset.is_valid():

                formset_data = []

                # for key, value in request.POST.items():
                #     if key.startswith('form-'):
                #         # Add other form fields as needed
                #         formset_data.append({key: value})


                for form in formset:
                    form_data = form.cleaned_data

                    # Convert Timeslot object to a serializable format
                    if 'timeslot' in form_data:
                        form_data['timeslot'] = form_data['timeslot'].dayTime.slot.strftime("%H:%M")  # Adjust this based on your Timeslot model

                    formset_data.append(form_data)
                # Store formset data in the session
                request.session['formset_data'] = formset_data

                #print(formset.cleaned_data)

                return HttpResponseRedirect(reverse('reservations:preview_reservation', args=(reservation_period_id, school_user_id,)) + f'?date={date}')

        elif formset.is_valid():

            if not request.user.is_superuser:

                #query current school year
                current_school_year = SchoolYear.objects.filter(start_date__lte=athens_now, end_date__gte=athens_now).first()
                if current_school_year:   
                    # Use Q objects to handle the OR condition for start and end dates
                    query = Q(schoolUser__creator=request.user) & Q(reservation_period__schoolYear=current_school_year)
                    # Filter reservations based on the current school year and the user
                    my_reservations_current_year_number = len(Reservation.objects.filter(query).exclude(status='denied'))
                    print(my_reservations_current_year_number)
                    if my_reservations_current_year_number:
                        my_reservation_period = ReservationPeriod.objects.filter(schoolYear=current_school_year).filter(reservation__schoolUser__creator=request.user).first()
                        print(my_reservation_period)
                    else:
                        my_reservation_period = res_period
                else:
                    my_reservations_current_year_number = 0

                # # Count the number of existing reservations for the user and reservation period
                # existing_reservations_count = Reservation.objects.filter(
                #     schoolUser__creator=request.user,
                #     reservation_period=res_period,
                # ).exclude(status='denied').count()

                # Count the number of existing reservations for the user on the selected date
                existing_reservations_on_date = Reservation.objects.filter(
                    schoolUser__creator=request.user,
                    reservation_period=res_period,
                    reservation_date=selected_calendar_date,
                ).exclude(status='denied').count()

                #if existing_reservations_count < 3 and existing_reservations_on_date < 3:
                # Count the number of forms submitted in the formset
                submitted_forms_count = len([form for form in formset.forms if form.cleaned_data.get('timeslot')])

                # Calculate the maximum allowed additional reservations
                max_additional_reservations = min(3 - my_reservations_current_year_number, 3 - existing_reservations_on_date)

                existing_reservation_dates = Reservation.objects.filter(schoolUser__creator=request.user,reservation_period=res_period,).values_list('reservation_date', flat=True)

                if len(set(existing_reservation_dates)) > 1 or (len(set(existing_reservation_dates)) == 1 and existing_reservation_dates[0] != selected_calendar_date.id):
                    context['different_selected_date_violation_error'] = 'Δικαιούστε να καταχωρίσετε αίτημα επίσκεψης σε μία μόνο ημερομηνία εντός του τρέχοντος σχολικού έτους.'
                else:
                    if submitted_forms_count <= max_additional_reservations and my_reservation_period == res_period:
                        # The user is allowed to make the requested number of reservations

                        # Process and save the reservations
                        for form in formset:
                            #my_reservations = Reservation.objects.filter(schoolUser__creator=request.user).filter(reservation_period=res_period)
                            if form.cleaned_data.get('timeslot'):
                                #if len(Reservation.objects.filter(schoolUser__creator=request.user).filter(reservation_period=res_period)) < 4 and len(Reservation.objects.filter(schoolUser__creator=request.user).filter(reservation_period=res_period).exclude(reservation_date=selected_calendar_date)) == 0:
                                my_reservation = Reservation(
                                    schoolUser=schoolUser,
                                    reservation_date=selected_calendar_date,
                                    timeslot=form.cleaned_data["timeslot"],
                                    teacher_number=form.cleaned_data["teacher_number"],
                                    student_number=form.cleaned_data["student_number"],
                                    amea=form.cleaned_data["amea"],
                                    terms_accepted=form.cleaned_data["terms_accepted"],
                                    reservation_period=res_period,
                                    updated_by = request.user
                                )
                                my_reservation.save()
                                my_reservations.append(my_reservation)

                        messages.add_message(request, messages.INFO, 'Καταχωρίσατε με επιτυχία την κράτησή σας!')
                        send_consolidated_reservation_registration_emails(my_reservations)

                        return redirect(reverse('reservations:my_reservations'))
                
                    else:
                        context['max_allowed_violation_error'] = 'Δικαιούστε να καταχωρίσετε αίτημα επίσκεψης για έως τρεις ομάδες μαθητών/τριών σε μία μόνο ημερομηνία.'

            else:
                for form in formset:
                        #my_reservations = Reservation.objects.filter(schoolUser__creator=request.user).filter(reservation_period=res_period)
                        if form.cleaned_data.get('timeslot'):
                            #if len(Reservation.objects.filter(schoolUser__creator=request.user).filter(reservation_period=res_period)) < 4 and len(Reservation.objects.filter(schoolUser__creator=request.user).filter(reservation_period=res_period).exclude(reservation_date=selected_calendar_date)) == 0:
                            my_reservation = Reservation(
                                schoolUser=schoolUser,
                                reservation_date=selected_calendar_date,
                                timeslot=form.cleaned_data["timeslot"],
                                teacher_number=form.cleaned_data["teacher_number"],
                                student_number=form.cleaned_data["student_number"],
                                amea=form.cleaned_data["amea"],
                                terms_accepted=form.cleaned_data["terms_accepted"],
                                reservation_period=res_period,
                                updated_by = request.user
                            )
                            my_reservation.save()
                            my_reservations.append(my_reservation)

                messages.add_message(request, messages.INFO, 'Καταχωρίσατε με επιτυχία την κράτησή σας!')
                send_consolidated_reservation_registration_emails(my_reservations)

                return redirect(reverse('schoolsadmin:school_reservations_admin' , kwargs={ 'school_id': schoolUser.id }))


            #return HttpResponseRedirect(reverse('reservations:my_reservations'))
        else:
            # Formset is not valid, include it in the context
            context['formset'] = formset
            # Include specific error messages in the context
            context['timeslot_error'] = any(formset.errors) and formset.errors[0].get('timeslot')
            context['terms_accepted_error'] = any(formset.errors) and formset.errors[0].get('terms_accepted')

    else:
        formset = ReservationFormSet(reservation_period=res_period, selected_date=date)

    context.update({
        'res_period': res_period,
        'reservation_period_id': reservation_period_id,
        'schoolUser': schoolUser,
        'school_user_id': school_user_id,
        'date': date,
        'week_day': selected_calendar_date_name,
        'selected_calendar_date_day': selected_calendar_date_day,
        'selected_calendar_date_month': selected_calendar_date_month,
        'selected_calendar_date_year': selected_calendar_date_year,
        'allowed_timeslots': allowed_timeslots,
        'occupied_timeslots': occupied_timeslots,
        'non_occupied_timeslots': non_occupied_timeslots,
        'non_occupied_timeslots_count': non_occupied_timeslots_count,
        'formset': formset,
        'exceptional_rules': ExceptionalRule.objects.filter(date = selected_calendar_date),
        'preview_different_selected_date_violation_error': preview_different_selected_date_violation_error,
        'preview_max_allowed_violation_error': preview_max_allowed_violation_error,
    })

    #return render(request, 'reservations/reservation2.html', context)

    if request.user.is_superuser:
        if selected_calendar_date.is_vacation:
            return render(request, 'reservations/reservation_vacation_admin.html', context)
        else:
            return render(request, 'reservations/reservation_admin.html', context)
    else:
        if selected_calendar_date.is_vacation:
            return render(request, 'reservations/reservation_vacation_user.html', context)
        else:
            return render(request, 'reservations/reservation_user.html', context)


@login_required
def preview_reservation(request, reservation_period_id, school_user_id):

    # Get current UTC time
    utc_now = datetime.now(pytz.utc)

    # Define the Athens time zone
    athens_tz = pytz.timezone('Europe/Athens')

    # Convert UTC time to Athens time
    athens_now = utc_now.astimezone(athens_tz)

    date = request.GET.get('date') or request.POST.get('date')
    res_period = get_object_or_404(ReservationPeriod, pk=reservation_period_id)

    selected_date = datetime.strptime(date, "%Y-%m-%d")
    selected_calendar_date = Day.objects.get(date=selected_date)
    selected_calendar_date_name = selected_calendar_date.date.strftime("%A")

    selected_calendar_date_day = selected_calendar_date.date.strftime("%d")
    selected_calendar_date_month = selected_calendar_date.date.strftime("%B")
    selected_calendar_date_year = selected_calendar_date.date.strftime("%Y")

    schoolUser = SchoolUser.objects.get(pk=school_user_id)

    formset_data = request.session.get('formset_data', [])

    my_reservations = []

    # Extract the data for each form from formset_data
    form_data_list = [data for data in formset_data if data]

    day_of_week_mapping = {
        'Monday': 'a',
        'Tuesday': 'b',
        'Wednesday': 'c',
        'Thursday': 'd',
        'Friday': 'e',
        'Saturday': 'f',
        'Sunday': 'g',
    }

    # Create a new formset with prefilled data
    ReservationFormSet = formset_factory(ReservationForm, extra=0, max_num=3, formset=BaseReservationFormSet)

    for form_data in form_data_list:

        # Convert the time back to Timeslot instance
        time_str = form_data['timeslot']
        selected_date_format = datetime.strptime(date, "%Y-%m-%d")
        day_of_week = day_of_week_mapping[selected_date_format.strftime('%A')]
        day_time = DayTime.objects.get(day=day_of_week, slot=time_str)
        form_data['timeslot'] = Timeslot.objects.filter(reservation_period=reservation_period_id, dayTime=day_time).first()
    
    formset = ReservationFormSet(request.POST or None, initial=form_data_list)

    redirect_url = reverse('reservations:make_reservation' , kwargs={ 'reservation_period_id': reservation_period_id, 'school_user_id': school_user_id, })
    redirect_url += f'?date={date}'

    # Disable fields for read-only display
    if 'preview_reservation' in request.path:
        for form in formset.forms:
            for field_name, field in form.fields.items():
                form.fields[field_name].widget.attrs['readonly'] = True
                #form.fields[field_name].widget.attrs['disabled'] = 'disabled'
            form.fields['timeslot'].widget.attrs['disabled'] = 'disabled'
            form.fields['student_number'].widget.attrs['disabled'] = 'disabled'
            form.fields['teacher_number'].widget.attrs['disabled'] = 'disabled'
            form.fields['amea'].widget.attrs['disabled'] = 'disabled'
            #form.fields['terms_accepted'].widget.attrs['disabled'] = 'disabled'

    # Handle form submission on the new page
    if request.method == 'POST':
        formset = ReservationFormSet(request.POST, reservation_period=res_period, selected_date=date)

        if formset.is_valid():

            if not request.user.is_superuser:

                #query current school year
                current_school_year = SchoolYear.objects.filter(start_date__lte=athens_now, end_date__gte=athens_now).first()
                if current_school_year:   
                    # Use Q objects to handle the OR condition for start and end dates
                    query = Q(schoolUser__creator=request.user) & Q(reservation_period__schoolYear=current_school_year)
                    # Filter reservations based on the current school year and the user
                    my_reservations_current_year_number = len(Reservation.objects.filter(query).exclude(status='denied'))
                else:
                    my_reservations_current_year_number = 0

                # # Count the number of existing reservations for the user and reservation period
                # existing_reservations_count = Reservation.objects.filter(
                #     schoolUser__creator=request.user,
                #     reservation_period=res_period,
                # ).exclude(status='denied').count()

                # Count the number of existing reservations for the user on the selected date
                existing_reservations_on_date = Reservation.objects.filter(
                    schoolUser__creator=request.user,
                    reservation_period=res_period,
                    reservation_date=selected_calendar_date,
                ).exclude(status='denied').count()

                #if existing_reservations_count < 3 and existing_reservations_on_date < 3:
                # Count the number of forms submitted in the formset
                submitted_forms_count = len([form for form in formset.forms if form.cleaned_data.get('timeslot')])

                # Calculate the maximum allowed additional reservations
                max_additional_reservations = min(3 - my_reservations_current_year_number, 3 - existing_reservations_on_date)


                existing_reservation_dates = Reservation.objects.filter(schoolUser__creator=request.user,reservation_period=res_period,).values_list('reservation_date', flat=True)

                if len(set(existing_reservation_dates)) > 1 or (len(set(existing_reservation_dates)) == 1 and existing_reservation_dates[0] != selected_calendar_date.id):
                    preview_different_selected_date_violation_error = 'Δικαιούστε να καταχωρίσετε αίτημα επίσκεψης σε μία μόνο ημερομηνία εντός του τρέχοντος σχολικού έτους.'
                    return redirect(redirect_url + f'&preview_different_selected_date_violation_error={preview_different_selected_date_violation_error}')
                else:


                    if submitted_forms_count <= max_additional_reservations:
                        # The user is allowed to make the requested number of reservations

                        # Process and save formset data to the model
                        for form_data in formset.cleaned_data:

                            # timeslot = form_data['timeslot'].id

                            # Reservation.objects.create(timeslot=timeslot, **form_data)  # Replace YourModel with the actual model name
                            selected_date_id = Day.objects.get(date=date).id

                            timeslot_instance = form_data.pop('timeslot')  # Remove 'timeslot' from form_data

                            timeslot_id = timeslot_instance.id

                            Reservation.objects.create(timeslot_id=timeslot_id, 
                                                    reservation_period=ReservationPeriod.objects.get(id=reservation_period_id), 
                                                    schoolUser=SchoolUser.objects.get(id=school_user_id),
                                                    reservation_date=Day.objects.get(id=selected_date_id),
                                                    updated_by=request.user,
                                                    **form_data)

                            my_reservation = Reservation(timeslot_id=timeslot_id, 
                                                    reservation_period=ReservationPeriod.objects.get(id=reservation_period_id), 
                                                    schoolUser=SchoolUser.objects.get(id=school_user_id),
                                                    reservation_date=Day.objects.get(id=selected_date_id),
                                                    updated_by=request.user,
                                                    **form_data)
                            my_reservations.append(my_reservation)
                        
                        messages.add_message(request, messages.INFO, 'Καταχωρίσατε με επιτυχία την κράτησή σας!')
                        send_consolidated_reservation_registration_emails(my_reservations)

                        # Clear the session data
                        request.session.pop('formset_data', None)

                        # Redirect to a success page or another view
                        # return HttpResponseRedirect(reverse('reservations:my_reservations'))
                        # if request.user.is_superuser:
                        #     return redirect(reverse('schoolsadmin:school_reservations_admin' , kwargs={ 'school_id': schoolUser.id }))
                        # else:
                        return redirect(reverse('reservations:my_reservations'))
                    
                    else:
                        preview_max_allowed_violation_error = 'Δικαιούστε να καταχωρίσετε αίτημα επίσκεψης για έως τρεις ομάδες μαθητών/τριών σε μία μόνο ημερομηνία.'
                        return redirect(redirect_url + f'&preview_max_allowed_violation_error={preview_max_allowed_violation_error}')
                    
            else:

                for form_data in formset.cleaned_data:

                    # timeslot = form_data['timeslot'].id

                    # Reservation.objects.create(timeslot=timeslot, **form_data)  # Replace YourModel with the actual model name
                    selected_date_id = Day.objects.get(date=date).id

                    timeslot_instance = form_data.pop('timeslot')  # Remove 'timeslot' from form_data
                    #print(timeslot_instance)
                    timeslot_id = timeslot_instance.id
                    #print(timeslot_id)
                    Reservation.objects.create(timeslot_id=timeslot_id, 
                                            reservation_period=ReservationPeriod.objects.get(id=reservation_period_id), 
                                            schoolUser=SchoolUser.objects.get(id=school_user_id),
                                            reservation_date=Day.objects.get(id=selected_date_id),
                                            updated_by=request.user,
                                            **form_data)

                    my_reservation = Reservation(timeslot_id=timeslot_id, 
                                            reservation_period=ReservationPeriod.objects.get(id=reservation_period_id), 
                                            schoolUser=SchoolUser.objects.get(id=school_user_id),
                                            reservation_date=Day.objects.get(id=selected_date_id),
                                            updated_by=request.user,
                                            **form_data)
                    my_reservations.append(my_reservation)
                
                messages.add_message(request, messages.INFO, 'Καταχωρίσατε με επιτυχία την κράτησή σας!')
                send_consolidated_reservation_registration_emails(my_reservations)

                # Clear the session data
                request.session.pop('formset_data', None)

                # Redirect to a success page or another view
                # return HttpResponseRedirect(reverse('reservations:my_reservations'))
                # if request.user.is_superuser:
                #     return redirect(reverse('schoolsadmin:school_reservations_admin' , kwargs={ 'school_id': schoolUser.id }))
                # else:
                return redirect(reverse('schoolsadmin:school_reservations_admin' , kwargs={ 'school_id': schoolUser.id }))
            
            # else:
            #     preview_max_allowed_violation_error = 'Δικαιούστε να καταχωρίσετε αίτημα επίσκεψης για έως τρεις ομάδες μαθητών/τριών σε μία μόνο ημερομηνία.'
            #     return redirect(redirect_url + f'&preview_max_allowed_violation_error={preview_max_allowed_violation_error}')

    if request.user.is_superuser:
        return render(request, 'reservations/preview_reservation_admin.html', {'formset': formset,
                                                                            'reservation_period_id': reservation_period_id,
                                                                            'school_user_id': school_user_id,
                                                                            'date': date,
                                                                            'selected_calendar_date': selected_calendar_date,
                                                                            'week_day': selected_calendar_date_name,
                                                                            'selected_calendar_date_day': selected_calendar_date_day,
                                                                            'selected_calendar_date_month': selected_calendar_date_month,
                                                                            'selected_calendar_date_year': selected_calendar_date_year,
                                                                            'schoolUser': schoolUser,
                                                                            })
    else:
        return render(request, 'reservations/preview_reservation_user.html', {'formset': formset,
                                                                            'reservation_period_id': reservation_period_id,
                                                                            'school_user_id': school_user_id,
                                                                            'date': date,
                                                                            'selected_calendar_date': selected_calendar_date,
                                                                            'week_day': selected_calendar_date_name,
                                                                            'selected_calendar_date_day': selected_calendar_date_day,
                                                                            'selected_calendar_date_month': selected_calendar_date_month,
                                                                            'selected_calendar_date_year': selected_calendar_date_year,
                                                                            'schoolUser': schoolUser,
                                                                            })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def calendar_timeslot(request, reservation_period_id, year=None, month=None):

    # Get current UTC time
    utc_now = datetime.now(pytz.utc)

    # Define the Athens time zone
    athens_tz = pytz.timezone('Europe/Athens')

    # Convert UTC time to Athens time
    athens_now = utc_now.astimezone(athens_tz)

    # If reservation_period_id is provided, get the start date of the reservation period
    if reservation_period_id:
        #reservation_period = ReservationPeriod.objects.get(pk=reservation_period_id)
        reservation_period = get_object_or_404(ReservationPeriod, pk=reservation_period_id)
        if not year and not month:
            start_date = reservation_period.start_date
        else: 
            start_date = date(year, month, 1)
    else:
        # If no reservation_period_id is provided, use the current date
        start_date = athens_now

    # If year and month are not provided, use the start date
    if not year:
        year = start_date.year
    if not month:
        month = start_date.month

    # Calculate previous and next months
    prev_month = start_date - timedelta(days=start_date.day)
    next_month = start_date + timedelta(days=(32 - start_date.day))


    # Retrieve days for the current month
    month_days = get_month_days(year, month, reservation_period_id)

    for week in month_days:
        for day in week:
            if isinstance(day, Day):
                day.exceptional_timeslots = ExceptionalRule.objects.filter(date=day)

    context = {
        #'current_month': f'{month}/{year}',
        'current_month': month,
        'current_year': year,
        'prev_year': prev_month.year,
        'prev_month': prev_month.month,
        'next_year': next_month.year,
        'next_month': next_month.month,
        'month_days': month_days,
        'reservation_period_id': reservation_period.id,
        'reservation_period': reservation_period,
    }

    return render(request, 'reservations/calendar_exceptional_timeslot.html', context)

@ login_required
def delete_reservation(request, reservation_id, school_user_id):
    delete_reservation = get_object_or_404(Reservation, id=reservation_id) 
    schoolUser = SchoolUser.objects.get(pk=school_user_id)
    error =''

    if delete_reservation.schoolUser.creator != request.user and not request.user.is_superuser:
        raise Http404("Αδυναμία πρόσβασης")
    else:
        if request.method == 'POST':    
            if delete_reservation.status == 'pending':
                delete_reservation.delete()                    
                if request.user.is_superuser:
                    return redirect(reverse('schoolsadmin:school_reservations_admin' , kwargs={ 'school_id': schoolUser.id }))
                else:
                    return redirect(reverse('reservations:my_reservations'))
            else:
                error = 'Μπορείτε να διαγράψετε μόνο εκκρεμείς κρατήσεις.'         

    return render(request, 'reservations/delete_reservation.html', {'delete_reservation': delete_reservation, 
                                                                    'schoolUser': schoolUser, 
                                                                    'error': error,
                                                                    'reservationDateName': delete_reservation.reservation_date.date.strftime("%A"),
                                                                    'reservationDateDay': delete_reservation.reservation_date.date.strftime("%d"),
                                                                    'reservationDateMonth': delete_reservation.reservation_date.date.strftime("%B"),
                                                                    'reservationDateYear': delete_reservation.reservation_date.date.year,
                                                                    })

@ login_required
def update_reservation(request, reservation_id, school_user_id):
    update_reservation = get_object_or_404(Reservation, id=reservation_id) 
    schoolUser = SchoolUser.objects.get(pk=school_user_id)
    reservationUpdateForm = ReservationUpdateForm(instance=update_reservation)

    if update_reservation.schoolUser.creator != request.user:
        raise Http404("Αδυναμία πρόσβασης")
    else:
        if request.method == 'POST':
            reservationUpdateForm = ReservationUpdateForm(request.POST, instance=update_reservation)
            if reservationUpdateForm.is_valid():
                reservationUpdateForm.save()
                print(update_reservation.updated_by)
                if request.user.is_superuser:
                    return redirect(reverse('schoolsadmin:school_reservations_admin' , kwargs={ 'school_id': schoolUser.id }))
                else:
                    return redirect(reverse('reservations:my_reservations'))

    return render(request, 'reservations/update_reservation.html', {'update_reservation':update_reservation, 
                                                                    'reservationUpdateForm': reservationUpdateForm,
                                                                    'schoolUser': schoolUser,
                                                                    'reservationDateName': update_reservation.reservation_date.date.strftime("%A"),
                                                                    'reservationDateDay': update_reservation.reservation_date.date.strftime("%d"),
                                                                    'reservationDateMonth': update_reservation.reservation_date.date.strftime("%B"),
                                                                    'reservationDateYear': update_reservation.reservation_date.date.year,                                                                    
                                                                    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def handle_reservations(request):

    # Get current UTC time
    utc_now = datetime.now(pytz.utc)

    # Define the Athens time zone
    athens_tz = pytz.timezone('Europe/Athens')

    # Convert UTC time to Athens time
    athens_now = utc_now.astimezone(athens_tz)

    available_res_periods = ReservationPeriod.objects.filter(is_available=True)
    context = {}

    if len(available_res_periods) > 0:
        dates = available_res_periods.values('start_date').order_by('start_date')
        closest_available_res_period = available_res_periods.filter(start_date=dates[0]['start_date'])
        candidate_reservations = Reservation.objects.filter(reservation_period=closest_available_res_period[0]).order_by('-created_at', 'schoolUser__school__name', 'timeslot__dayTime__slot')
        context['closest_available_res_period'] = closest_available_res_period[0]
        context['candidate_reservations'] = candidate_reservations
        context['candidate_reservations_num'] = len(candidate_reservations)
    else:
        context['no_available_res_period'] = 'Δεν έχετε δηλώσει καμία περίοδο επισκέψεων ως διαθέσιμη για κρατήσεις.'

    if request.method == 'POST':
        reservation_ids = request.POST.getlist('reservation_ids')
        action = request.POST.get('action')

        reservations = Reservation.objects.filter(id__in=reservation_ids)
        # Get the current user
        current_user = request.user

        with transaction.atomic():
            for reservation in reservations:

                if action == 'approve':
                    reservation.status = 'approved'
                elif action == 'deny':
                    reservation.status = 'denied'
                elif action == 'performed':
                    reservation.is_performed = True
                elif action == 'nonperformed':
                    reservation.is_performed = False

                reservation.updated_at = athens_now
                reservation.updated_by = current_user
                print(current_user)
                reservation.save()

        messages.success(request, f'Επιτυχής ενημέρωση {len(reservations)} κρατήσεων.')

        if action in ['approve', 'deny']:
            send_consolidated_reservation_emails(reservations)

        # if action == 'approve':
        #     reservations.update(status='approved', updated_at=athens_now, updated_by=current_user)
        #     #context['approve_message'] = 'Εγκρίνατε με επιτυχία τις επιλεγμένες κρατήσεις.'
        #     messages.success(request, 'Εγκρίνατε με επιτυχία τις επιλεγμένες κρατήσεις.')
        #     # Send a consolidated email to each user
        #     send_consolidated_reservation_emails(reservations)
        # elif action == 'deny':
        #     reservations.update(status='denied', updated_at=athens_now, updated_by=current_user)
        #     #context['deny_message'] = 'Απορρίψατε με επιτυχία τις επιλεγμένες κρατήσεις.'
        #     messages.success(request, 'Απορρίψατε με επιτυχία τις επιλεγμένες κρατήσεις.')
        #     # Send a consolidated email to each user
        #     send_consolidated_reservation_emails(reservations)
        # elif action == 'performed':
        #     reservations.update(is_performed=True, updated_at=athens_now, updated_by=current_user)
        #     #context['performed_message'] = 'Αλλάξατε με επιτυχία την κατάσταση των επιλεγμένων κρατήσεων σε πραγματοποιημένες.'
        #     messages.success(request, 'Αλλάξατε με επιτυχία την κατάσταση των επιλεγμένων κρατήσεων σε πραγματοποιημένες.')
        # elif action == 'nonperformed':
        #     reservations.update(is_performed=False, updated_at=athens_now, updated_by=current_user)
        #     #context['nonperformed_message'] = 'Αλλάξατε με επιτυχία την κατάσταση των επιλεγμένων κρατήσεων σε μη πραγματοποιημένες.'
        #     messages.success(request, 'Αλλάξατε με επιτυχία την κατάσταση των επιλεγμένων κρατήσεων σε μη πραγματοποιημένες.')

        # Redirect to the previous page or any desired URL
        return redirect(reverse('reservations:handle_reservations'))
    
    # context.update({
    #     'closest_available_res_period': closest_available_res_period, 
    #     'candidate_reservations': candidate_reservations, 
    # })

    return render(request, 'reservations/handle_reservations.html', context)


# Send a consolidated email to each user
def send_consolidated_reservation_emails(reservations):
    # Group reservations by user
    user_reservations = {}
    for reservation in reservations:
        user_id = reservation.schoolUser.id
        if user_id not in user_reservations:
            user_reservations[user_id] = []
        user_reservations[user_id].append(reservation)

    # Send a consolidated email to each user
    for user_id, user_reservations_list in user_reservations.items():
        user = user_reservations_list[0].schoolUser.creator  # Assuming user is a ForeignKey in Reservation model
        send_consolidated_email(user, user_reservations_list)

# Send a consolidated email to a user
def send_consolidated_email(user, reservations):
    # Customize the email subject and message based on your requirements
    subject = 'Επίσκεψη στη Βουλή των Ελλήνων'

    # Create an HTML version of your email content
    html_message = render_to_string('email_templates/consolidated_reservations.html', {
        'reservations': reservations,
    })

    athens_time = timezone.localtime(timezone.now(), timezone=timezone.get_current_timezone())

    # Send the email
    send_mail(
        subject,
        'This is a plain text version of your email content.',
        'admin@parliament.foundation',
        [user.email], 
        fail_silently=False,
        html_message=html_message,
    )

# Send a consolidated email to each user
def send_consolidated_reservation_registration_emails(reservations):
    # Group reservations by user
    user_reservations = {}
    for reservation in reservations:
        user_id = reservation.schoolUser.id
        if user_id not in user_reservations:
            user_reservations[user_id] = []
        user_reservations[user_id].append(reservation)

    # Send a consolidated email to each user
    for user_id, user_reservations_list in user_reservations.items():
        user = user_reservations_list[0].schoolUser.creator  # Assuming user is a ForeignKey in Reservation model
        send_consolidated_registration_email(user, user_reservations_list)

# Send a consolidated email to a user
def send_consolidated_registration_email(user, reservations):
    # Customize the email subject and message based on your requirements
    subject = 'Επίσκεψη στη Βουλή των Ελλήνων'

    # Create an HTML version of your email content
    html_message = render_to_string('email_templates/consolidated_reservations_registration.html', {
        'reservations': reservations,
    })

    athens_time = timezone.localtime(timezone.now(), timezone=timezone.get_current_timezone())

    # Encode the subject to base64
    encoded_subject = base64.b64encode(subject.encode('utf-8')).decode('utf-8')


    # Send the email
    email = EmailMessage(
        '=?utf-8?b?{}?='.format(encoded_subject), 
        'This is a plain text version of your email content.\n\n' + html_message,  # Combine plain text and HTML
        'admin@parliament.foundation',
        [user.email],
    )

    # Add a custom 'Date' header
    email.extra_headers['Date'] = athens_time.strftime('%a, %d %b %Y %H:%M:%S %z')

    # Send the email
    email.send(fail_silently=True)
             
@ login_required
@user_passes_test(lambda u: u.is_superuser)                                                       
def update_reservation_admin(request, reservation_id):

    # Get current UTC time
    utc_now = datetime.now(pytz.utc)

    # Define the Athens time zone
    athens_tz = pytz.timezone('Europe/Athens')

    # Convert UTC time to Athens time
    athens_now = utc_now.astimezone(athens_tz)

    #update_reservation = get_object_or_404(Reservation, id=reservation_id)
    update_reservation = Reservation.objects.get(id=reservation_id)
    schoolUser = update_reservation.schoolUser

    if request.method == 'POST':
        # form = ReservationUpdateAdminForm(request.POST, instance=update_reservation)
        reservation_date = request.POST.get('reservation_date_')
        timeslot = request.POST.get('timeslot')
        student_number = request.POST.get('student_number')
        teacher_number = request.POST.get('teacher_number')
        amea = request.POST.get('amea')        

        reservation_date_instance = Day.objects.get(date=datetime.strptime(reservation_date, "%Y-%m-%d"))
        timeslot_instance = Timeslot.objects.get(id=timeslot)

        # print(datetime.strptime(reservation_date, "%Y-%m-%d"))
        # print(timeslot)
        # print(amea)

        update_reservation.reservation_date = reservation_date_instance
        update_reservation.timeslot = timeslot_instance
        update_reservation.student_number = student_number
        update_reservation.teacher_number = teacher_number
        if amea is None:
            update_reservation.amea = False
        else:
            update_reservation.amea = True
        update_reservation.updated_at = athens_now
        #print(request.user)
        update_reservation.updated_by = request.user
        update_reservation.save()

        user = schoolUser.creator

        send_reservation_update_email(user, update_reservation)

        #     messages.success(request, 'Reservation updated successfully.')
        next = request.POST.get('next')
        #return redirect(reverse('reservations:handle_reservations'))
        return HttpResponseRedirect(next)
    else:
        form = ReservationUpdateAdminForm(instance=update_reservation, initial={'reservation_date': update_reservation.reservation_date.date})

    return render(request, 'reservations/update_reservations_admin.html', {'form': form, 
                                                            'update_reservation': update_reservation,
                                                            'schoolUser': schoolUser,
                                                            'reservationDateName': update_reservation.reservation_date.date.strftime("%A"),
                                                            'reservationDateDay': update_reservation.reservation_date.date.strftime("%d"),
                                                            'reservationDateMonth': update_reservation.reservation_date.date.strftime("%B"),
                                                            'reservationDateYear': update_reservation.reservation_date.date.year,     
                                                             })

def send_reservation_update_email(user, reservation):
    amea_mapping = {True: 'ΝΑΙ', False: 'ΟΧΙ'}

    subject = 'Επίσκεψη στη Βουλή των Ελλήνων'
    
    # Create an HTML version of your email content
    html_message = render_to_string('email_templates/reservation_update.html', {
        'reservation_date': reservation.reservation_date.date,
        'reservation_time': reservation.timeslot.dayTime.slot,
        'student_number': reservation.student_number,
        'teacher_number': reservation.teacher_number,
        'amea': amea_mapping[reservation.amea],
    })

    # Send the email
    send_mail(
        subject,
        'This is a plain text version of your email content.',
        'admin@parliament.foundation',
        [user.email], 
        fail_silently=False,
        html_message=html_message,
    )

                                                                    
@ login_required
@user_passes_test(lambda u: u.is_superuser)   
def reservation_history(request, reservation_id):
    reservation = get_object_or_404(Reservation, id=reservation_id)
    schoolUser = reservation.schoolUser
    #history = reservation.history.all()  # Fetch all historical records

    field_mapping = {'reservation_date': 'ημερομηνία', 
                    'timeslot': 'ώρα', 
                    'amea': 'ΑΜΕΑ', 
                    'student_number': 'αριθμός μαθητών/τριων',
                    'teacher_number': 'αριθμός εκπαιδευτικών',
                    'status': 'κατάσταση',
                    'is_performed': 'πραγματοποίηση επίσκεψης',
                    'updated_by': 'χρήστης ενημέρωσης'}
    
    amea_mapping = {True: 'ΝΑΙ', 
                    False: 'ΟΧΙ', 
                    }

    status_mapping = {
        'pending': 'εκκρεμής',
        'denied': 'ακυρωμένη',
        'approved': 'επιβεβαιωμένη',
    }

    is_performed_mapping = {True: 'πραγματοποιημένη', 
                    False: 'μη πραγματοποιημένη', 
                    }

    history_changes = []

    # Define the Athens time zone
    athens_tz = pytz.timezone('Europe/Athens')

    for i in range(1,len(reservation.history.all())):
        new_record, old_record = reservation.history.all()[i-1], reservation.history.all()[i]
        delta = new_record.diff_against(old_record)
        for change in delta.changes:
            formatted_time = reservation.history.all()[i-1].history_date.astimezone(pytz.timezone('Europe/Athens')).strftime("%d/%m/%Y, %H:%M:%S")
            if change.field == 'timeslot':
                history_changes.append("Την {} το πεδίο {} άλλαξε από {} σε {} από τον χρήστη {}".format(formatted_time, field_mapping[change.field], Timeslot.objects.get(id=change.old).dayTime.slot.strftime("%H:%M"), Timeslot.objects.get(id=change.new).dayTime.slot.strftime("%H:%M"), reservation.history.all()[i].history_user))
            if change.field == 'reservation_date':
                history_changes.append("Την {} το πεδίο {} άλλαξε από {} σε {} από τον χρήστη {}".format(formatted_time, field_mapping[change.field], Day.objects.get(id=change.old).date.strftime("%d/%m/%Y"), Day.objects.get(id=change.new).date.strftime("%d/%m/%Y"), reservation.history.all()[i-1].history_user))
            if change.field == 'amea':
                history_changes.append("Την {} το πεδίο {} άλλαξε από {} σε {} από τον χρήστη {}".format(formatted_time, field_mapping[change.field], amea_mapping[change.old], amea_mapping[change.new], reservation.history.all()[i-1].history_user))
            if change.field == 'student_number':
                history_changes.append("Την {} το πεδίο {} άλλαξε από {} σε {} από τον χρήστη {}".format(formatted_time, field_mapping[change.field], change.old, change.new, reservation.history.all()[i-1].history_user))
            if change.field == 'teacher_number':
                history_changes.append("Την {} το πεδίο {} άλλαξε από {} σε {} από τον χρήστη {}".format(formatted_time, field_mapping[change.field], change.old, change.new, reservation.history.all()[i-1].history_user))                 
            if change.field == 'status':
                history_changes.append("Την {} το πεδίο {} άλλαξε από {} σε {} από τον χρήστη {}".format(formatted_time, field_mapping[change.field], status_mapping[change.old], status_mapping[change.new], reservation.history.all()[i-1].history_user))                 
            if change.field == 'is_performed':
                history_changes.append("Την {} το πεδίο {} άλλαξε από {} σε {} από τον χρήστη {}".format(formatted_time, field_mapping[change.field], is_performed_mapping[change.old], is_performed_mapping[change.new], reservation.history.all()[i-1].history_user))                 
            # if change.field == 'updated_by':
            #     history_changes.append("Την {} το πεδίο {} άλλαξε από {} σε {} από τον χρήστη {}".format(formatted_time, field_mapping[change.field], change.old, change.new, reservation.history.all()[i].updated_by))                 

    return render(request, 'reservations/reservation_history2.html', {'reservation': reservation, 
                                                                      'history_changes': history_changes, 
                                                                      'schoolUser': schoolUser,
                                                                      })   


@ login_required
@user_passes_test(lambda u: u.is_superuser)   
def calendar_reservations_res_period_selection(request):

    form = ReservationCalendarByDateForm()
    context = {}

    selected_reservation_period_id = request.GET.get('reservation_period')

    # Check if the Filter button is clicked
    if request.GET.get('filter') == '1' and selected_reservation_period_id:
        # Reset selected values
        form = ReservationCalendarByDateForm()
        return redirect('reservations:calendar_reservations', reservation_period_id=selected_reservation_period_id)
    
    if request.GET.get('filter') == '1' and selected_reservation_period_id == '':
        context['error_message'] = 'Πρέπει να διαλέξετε μία περίοδο επισκέψεων'

    if request.GET.get('filter') == '2':
        form = ReservationCalendarByDateForm()

    context.update({
        'form': form
    })

    return render(request, 'reservations/calendar_reservations_res_period_selection.html', context)

@ login_required
@user_passes_test(lambda u: u.is_superuser)   
def reservation_dashboard(request):

    form = ReservationDashboardForm(request.GET)
    context = {}

    school_years = SchoolYear.objects.all()
    historical_reservations = Reservation.objects.all().order_by('reservation_period__start_date', 'reservation_date__date')
    reservation_periods = ReservationPeriod.objects.all()
    departments = Department.objects.all()
    school_users = SchoolUser.objects.all()

    # Initialize variables for selected options
    selected_school_year_id = request.GET.get('school_year')
    #print(selected_school_year_id)
    selected_reservation_period_id = request.GET.get('reservation_period')
    #print(selected_reservation_period_id)
    selected_department_id = request.GET.get('department')
    #print(selected_department_id)
    selected_school_user_id = request.GET.get('school_user')
    #print(selected_school_user_id)

    # Update the form's initial choices based on the selected school year
    if selected_school_year_id:
        form.fields['reservation_period'].choices = [("", "Επιλογή...")] + [(period.id, period.name) for period in ReservationPeriod.objects.filter(schoolYear_id=selected_school_year_id)]

    # Update the form's initial choices based on the selected school year and reservation period
    if selected_school_year_id and selected_reservation_period_id:
        form.fields['department'].choices = [("", "Επιλογή...")] + [(department.id, department.name) for department in Department.objects.filter(schooluser__reservation__reservation_period_id=selected_reservation_period_id).distinct()]

    # Update the form's initial choices based on the selected school year, reservation period, and department
    if selected_school_year_id and selected_reservation_period_id and selected_department_id:
        form.fields['school_user'].choices = [("", "Επιλογή...")] + [(user.id, user.school.name) for user in SchoolUser.objects.filter(department_id=selected_department_id).filter(reservation__reservation_period_id=selected_reservation_period_id).distinct()]

    if form.is_valid():
        selected_school_year_id = form.cleaned_data.get('school_year')
        selected_reservation_period_id = form.cleaned_data.get('reservation_period')
        selected_department_id = form.cleaned_data.get('department')
        selected_school_user_id = form.cleaned_data.get('school_user')

    else:
        print(form.errors)  # Print form errors for debugging

    if selected_school_year_id != '' and selected_school_year_id is not None:
        historical_reservations = historical_reservations.filter(reservation_period__schoolYear=selected_school_year_id).order_by('reservation_period__start_date', 'reservation_date__date')
        # reservation_periods = ReservationPeriod.objects.filter(schoolYear_id=selected_school_year_id)

    if selected_reservation_period_id != '' and selected_reservation_period_id is not None:
        historical_reservations = historical_reservations.filter(reservation_period=selected_reservation_period_id).order_by('reservation_period__start_date', 'reservation_date__date')
        # departments = Department.objects.filter(schooluser__reservation__reservation_period_id=selected_reservation_period_id).distinct()

    if selected_department_id != '' and selected_department_id is not None:
        historical_reservations = historical_reservations.filter(schoolUser__department=selected_department_id).order_by('reservation_period__start_date', 'reservation_date__date')
        # school_users = SchoolUser.objects.filter(department_id=selected_department_id).filter(reservation__reservation_period_id=selected_reservation_period_id)

    if selected_school_user_id != '' and selected_school_user_id is not None:
        historical_reservations = historical_reservations.filter(schoolUser=selected_school_user_id).filter(reservation_period_id=selected_reservation_period_id).order_by('reservation_period__start_date', 'reservation_date__date')

    if request.GET.get('filter') == '2':
        form = ReservationDashboardForm()

    historical_reservations_num = historical_reservations.count()

    # Check if the Filter button is clicked
    if request.GET.get('filter') == '1':
        # Reset selected values
        form = ReservationDashboardForm()
        context['filter'] = 'filter'

    context.update({
        'form': form,
        'school_years': school_years,
        'selected_school_year': int(selected_school_year_id) if selected_school_year_id else None,
        'reservation_periods': reservation_periods,
        'selected_reservation_period': int(selected_reservation_period_id) if selected_reservation_period_id else None,
        'departments': departments,
        'selected_department': int(selected_department_id) if selected_department_id else None,
        'school_users': school_users,
        'selected_school_user': int(selected_school_user_id) if selected_school_user_id else None,
        'historical_reservations': historical_reservations,
        'historical_reservations_num': historical_reservations_num,
    })

    return render(request, 'reservations/reservation_dashboard2.html', context)

def get_reservation_periods(request):
    # Get the school year ID from the AJAX request
    school_year_id = request.GET.get('school_year_id')

    # Retrieve reservation periods for the selected school year
    reservation_periods = ReservationPeriod.objects.filter(schoolYear_id=school_year_id).order_by('start_date')

    # Prepare the HTML options for the reservation period dropdown
    options = '<option value="">Επιλογή...</option>'
    for period in reservation_periods:
        options += f'<option value="{period.id}">{period.name}</option>'

    # Return the HTML options as JSON response
    return JsonResponse({'options': options})

def get_departments(request):
    reservation_period_id = request.GET.get('reservation_period_id')

    # Query departments based on the selected reservation period
    departments = Department.objects.filter(
        schooluser__reservation__reservation_period_id=reservation_period_id
    ).distinct()

    options = '<option value="">Επιλογή...</option>'
    for dept in departments:
        options += f'<option value="{dept.id}">{dept.name}</option>'

    return JsonResponse({'options': options})

def get_schoolusers(request):
    reservation_period_id = request.GET.get('reservation_period_id')
    department_id = request.GET.get('department_id')

    #Query school users based on the selected department and reservation period
    school_users = SchoolUser.objects.filter(
        department_id=department_id,
        reservation__reservation_period_id=reservation_period_id
    ).distinct()

    # school_users = SchoolUser.objects.filter(
    #     Q(department_id=department_id, reservation__reservation_period_id=reservation_period_id) &
    #     ~Q(reservation__status='denied')
    # ).distinct()

    options = '<option value="">Επιλογή...</option>'
    for user in school_users:
        options += f'<option value="{user.id}">{user.school.name}</option>'

    return JsonResponse({'options': options})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def calendar_reservations(request, reservation_period_id, year=None, month=None):

    # Get current UTC time
    utc_now = datetime.now(pytz.utc)

    # Define the Athens time zone
    athens_tz = pytz.timezone('Europe/Athens')

    # Convert UTC time to Athens time
    athens_now = utc_now.astimezone(athens_tz)

    # If reservation_period_id is provided, get the start date of the reservation period
    if reservation_period_id:
        #reservation_period = ReservationPeriod.objects.get(pk=reservation_period_id)
        reservation_period = get_object_or_404(ReservationPeriod, pk=reservation_period_id)
        if not year and not month:
            start_date = reservation_period.start_date
        else: 
            start_date = date(year, month, 1)
    else:
        # If no reservation_period_id is provided, use the current date
        start_date = athens_now

    # If year and month are not provided, use the start date
    if not year:
        year = start_date.year
    if not month:
        month = start_date.month

    # Calculate previous and next months
    prev_month = start_date - timedelta(days=start_date.day)
    next_month = start_date + timedelta(days=(32 - start_date.day))


    # Retrieve days for the current month
    month_days = get_month_days(year, month, reservation_period_id)

    for week in month_days:
        for day in week:
            if isinstance(day, Day):
                day.availability_percentage = calculate_availability_percentage(day.date, reservation_period_id)
                day.reservations_on_date = Reservation.objects.filter(reservation_date=day)

    context = {
        #'current_month': f'{month}/{year}',
        'current_month': month,
        'current_year': year,
        'prev_year': prev_month.year,
        'prev_month': prev_month.month,
        'next_year': next_month.year,
        'next_month': next_month.month,
        'month_days': month_days,
        'reservation_period_id': reservation_period.id,
        'reservation_period': reservation_period,
    }

    return render(request, 'reservations/calendar_reservations.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def reservation_details_by_date(request):

    date = str(request.GET.get('date'))

    # Parse the date string into a datetime object
    # date_obj = datetime.strptime(date, '%Y-%m-%d')

    # Query reservations for the given date
    reservations = Reservation.objects.filter(reservation_date__date=date).exclude(status='denied').order_by('timeslot__dayTime__slot')

    context = {'date': date, 'reservations': reservations}
    return render(request, 'reservations/reservation_details_table.html', context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def statistics_per_period(request, reservation_id):

    reservation_period = get_object_or_404(ReservationPeriod, pk=reservation_id)
    context = {}

    if reservation_period:
        res_num = Reservation.objects.filter(reservation_period=reservation_period).exclude(status='denied').count()
        school_num = SchoolUser.objects.filter(reservation__reservation_period_id=reservation_period).distinct().count()
        dept_num = Department.objects.filter(schooluser__reservation__reservation_period_id=reservation_period).distinct().count()
        total_students = Reservation.objects.filter(reservation_period=reservation_period).exclude(status='denied').aggregate(total_students=Sum(Cast('student_number', IntegerField())))
    else:
        context['error'] = 'Δεν έχετε επιλέξει έγκυρη περίοδο επισκέψεων'

    context.update({
        'res_num': res_num, 
        'school_num': school_num, 
        'dept_num': dept_num,
        'total_students': total_students['total_students'],
        'reservation_period': reservation_period,
    })

    return render(request, 'reservations/statistics_per_period.html', context)

def reservationsPerDayResPeriod(request, reservation_id):

    reservation_period = get_object_or_404(ReservationPeriod, pk=reservation_id)
    days = Day.objects.filter(date__gte=reservation_period.start_date, date__lte=reservation_period.end_date).order_by('date')
    
    #fill in chart dates
    chart_days = []

    for i in range(len(days)):
        chart_days.append(datetime.strftime(days[i].date, "%d/%m/%Y"))

    #fill in reservation number
    res_num=[]

    for i in range(len(days)):
        res_num.append(Reservation.objects.filter(reservation_date=days[i]).exclude(status='denied').count())

    #json dict
    reservations_per_day=[]
    for i in range(len(chart_days)):
        reservations_per_day.append({chart_days[i]:res_num[i]})

    return JsonResponse(reservations_per_day, safe=False)

def studentsPerDayResPeriod(request, reservation_id):

    reservation_period = get_object_or_404(ReservationPeriod, pk=reservation_id)
    days = Day.objects.filter(date__gte=reservation_period.start_date, date__lte=reservation_period.end_date).order_by('date')
    
    #fill in chart dates
    chart_days = []

    for i in range(len(days)):
        chart_days.append(datetime.strftime(days[i].date, "%d/%m/%Y"))

    #fill in reservation number
    stud_num=[]

    for i in range(len(days)):
        students = Reservation.objects.filter(reservation_date=days[i]).exclude(status='denied').aggregate(total_students=Sum(Cast('student_number', IntegerField())))
        stud_num.append(students['total_students'])

    #json dict
    students_per_day=[]
    for i in range(len(chart_days)):
        students_per_day.append({chart_days[i]:stud_num[i]})

    return JsonResponse(students_per_day, safe=False)

def reservationsPerDeptResPeriod(request, reservation_id):

    reservation_period = get_object_or_404(ReservationPeriod, pk=reservation_id)

    departments = Department.objects.filter(
        schooluser__reservation__reservation_period_id=reservation_id
    ).distinct()
    
    #fill in chart departments
    chart_depts = []

    for i in range(len(departments)):
        chart_depts.append(departments[i].name)

    #fill in reservation number
    res_num_dept=[]

    for i in range(len(departments)):
        res_num_dept.append(Reservation.objects.filter(reservation_period=reservation_period).filter(schoolUser__department__id=departments[i].id).exclude(status='denied').count())

    #json dict
    reservations_per_dept=[]
    for i in range(len(chart_depts)):
        reservations_per_dept.append({chart_depts[i]:res_num_dept[i]})

    return JsonResponse(reservations_per_dept, safe=False)

def schoolsPerDeptResPeriod(request, reservation_id):

    reservation_period = get_object_or_404(ReservationPeriod, pk=reservation_id)

    departments = Department.objects.filter(
        schooluser__reservation__reservation_period_id=reservation_id
    ).distinct()
    
    #fill in chart departments
    chart_depts = []

    for i in range(len(departments)):
        chart_depts.append(departments[i].name)

    #fill in school number
    schoolnum_dept=[]

    for i in range(len(departments)):
        school_users = SchoolUser.objects.filter(
            Q(department_id=departments[i].id, reservation__reservation_period=reservation_period) &
            ~Q(reservation__status='denied')
        ).distinct()
        schoolnum_dept.append(school_users.distinct().count())

    #json dict
    schoolusers_per_dept=[]
    for i in range(len(chart_depts)):
        schoolusers_per_dept.append({chart_depts[i]:schoolnum_dept[i]})

    return JsonResponse(schoolusers_per_dept, safe=False)

def reservationsPerStatusResPeriod(request, reservation_id):

    reservation_period = get_object_or_404(ReservationPeriod, pk=reservation_id)

    volumes = []
    status_names = ['Εκκρεμείς', 'Επιβεβαιωμένες', 'Ακυρωμένες',]

    volumes.append(Reservation.objects.filter(reservation_period=reservation_period).filter(status='pending').count())
    volumes.append(Reservation.objects.filter(reservation_period=reservation_period).filter(status='approved').count())
    volumes.append(Reservation.objects.filter(reservation_period=reservation_period).filter(status='denied').count())

    volumes_per_status = []
    for i in range(len(volumes)):
        volumes_per_status.append({status_names[i]:volumes[i]})

    return JsonResponse(volumes_per_status, safe=False)

def reservationsPerPerformedResPeriod(request, reservation_id):

    reservation_period = get_object_or_404(ReservationPeriod, pk=reservation_id)

    volumes = []
    performed_names = ['Πραγματοποιημένες', 'Μη Πραγματοποιημένες',]

    volumes.append(Reservation.objects.filter(reservation_period=reservation_period).filter(is_performed=True).count())
    volumes.append(Reservation.objects.filter(reservation_period=reservation_period).filter(is_performed=False).count())

    volumes_per_performed = []
    for i in range(len(volumes)):
        volumes_per_performed.append({performed_names[i]:volumes[i]})

    return JsonResponse(volumes_per_performed, safe=False)

def reservationsPerTimeslotResPeriod(request, reservation_id):

    reservation_period = get_object_or_404(ReservationPeriod, pk=reservation_id)
    reservations_per_hour = Reservation.objects.filter(reservation_period=reservation_period).exclude(status='denied').values('timeslot__dayTime__slot').annotate(count=Count('id')).order_by('timeslot__dayTime__slot')

    timeslots = []
    res_per_timeslot = []

    for key, group in groupby(reservations_per_hour, key=lambda x: x['timeslot__dayTime__slot']):
        timeslots.append(key.strftime('%H:%M'))
        res_per_timeslot.append(sum(item['count'] for item in group))

    volumes_per_timeslot = []
    for i in range(len(timeslots)):
        volumes_per_timeslot.append({timeslots[i]:res_per_timeslot[i]})

    return JsonResponse(volumes_per_timeslot, safe=False)
    

@login_required
@user_passes_test(lambda u: u.is_superuser)
def statistics_per_year(request, schoolYear_id):

    school_year = get_object_or_404(SchoolYear, pk=schoolYear_id)
    context = {}

    if school_year:
        res_num = Reservation.objects.filter(reservation_period__schoolYear=school_year).exclude(status='denied').count()
        school_num = SchoolUser.objects.filter(reservation__reservation_period__schoolYear=school_year).distinct().count()
        dept_num = Department.objects.filter(schooluser__reservation__reservation_period__schoolYear=school_year).distinct().count()
        total_students = Reservation.objects.filter(reservation_period__schoolYear=school_year).exclude(status='denied').aggregate(total_students=Sum(Cast('student_number', IntegerField())))
    else:
        context['error'] = 'Δεν έχετε επιλέξει έγκυρο σχολικό έτος'

    context.update({
        'res_num': res_num, 
        'school_num': school_num, 
        'dept_num': dept_num,
        'total_students': total_students['total_students'],
        'school_year': school_year,
    })

    return render(request, 'reservations/statistics_per_year.html', context)

def reservationsPerDaySchoolYear(request, schoolYear_id):

    school_year = get_object_or_404(SchoolYear, pk=schoolYear_id)
    days = Day.objects.filter(date__gte=school_year.start_date, date__lte=school_year.end_date).order_by('date')
    
    #fill in chart dates
    chart_days = []

    for i in range(len(days)):
        chart_days.append(datetime.strftime(days[i].date, "%d/%m/%Y"))

    #fill in reservation number
    res_num=[]

    for i in range(len(days)):
        res_num.append(Reservation.objects.filter(reservation_date=days[i]).exclude(status='denied').count())

    #json dict
    reservations_per_day=[]
    for i in range(len(chart_days)):
        reservations_per_day.append({chart_days[i]:res_num[i]})

    return JsonResponse(reservations_per_day, safe=False)

def reservationsPerResPeriodSchoolYear(request, schoolYear_id):

    res_per = ReservationPeriod.objects.filter(schoolYear_id=schoolYear_id).order_by('start_date')
    res_per_values = ReservationPeriod.objects.filter(schoolYear_id=schoolYear_id).order_by('start_date').values('name')

    #fill in reservation periods
    res_periods = []

    for i in range(len(res_per_values)):
        res_periods.append(res_per_values[i]['name'])

    #fill in number of reservations per reservation period
    res_per_res_period = []

    for i in range(len(res_per)):
        res_per_res_period.append(Reservation.objects.filter(reservation_period=res_per[i]).exclude(status='denied').count())

    volumes_per_res_period = []
    for i in range(len(res_periods)):
        volumes_per_res_period.append({res_periods[i]:res_per_res_period[i]})

    return JsonResponse(volumes_per_res_period, safe=False)

def reservationsPerDeptSchoolYear(request, schoolYear_id):

    school_year = get_object_or_404(SchoolYear, pk=schoolYear_id)

    departments = Department.objects.filter(
        schooluser__reservation__reservation_period__schoolYear=school_year
    ).distinct()
    
    #fill in chart departments
    chart_depts = []

    for i in range(len(departments)):
        chart_depts.append(departments[i].name)

    #fill in reservation number
    res_num_dept=[]

    for i in range(len(departments)):
        res_num_dept.append(Reservation.objects.filter(reservation_period__schoolYear=school_year).filter(schoolUser__department__id=departments[i].id).exclude(status='denied').count())

    #json dict
    reservations_per_dept=[]
    for i in range(len(chart_depts)):
        reservations_per_dept.append({chart_depts[i]:res_num_dept[i]})

    return JsonResponse(reservations_per_dept, safe=False)

def studentsPerResPeriodSchoolYear(request, schoolYear_id):

    res_per = ReservationPeriod.objects.filter(schoolYear_id=schoolYear_id).order_by('start_date')
    res_per_values = ReservationPeriod.objects.filter(schoolYear_id=schoolYear_id).order_by('start_date').values('name')

    #fill in reservation periods
    res_periods = []

    for i in range(len(res_per_values)):
        res_periods.append(res_per_values[i]['name'])

    #fill in student number
    stud_num=[]

    for i in range(len(res_periods)):
        students = Reservation.objects.filter(reservation_period=res_per[i]).exclude(status='denied').aggregate(total_students=Sum(Cast('student_number', IntegerField())))
        stud_num.append(students['total_students'])

    #json dict
    students_per_res_period=[]
    for i in range(len(res_periods)):
        students_per_res_period.append({res_periods[i]:stud_num[i]})

    return JsonResponse(students_per_res_period, safe=False)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def statistics_all_years(request):

    context = {}

    res_num = Reservation.objects.exclude(status='denied').count()
    school_users_with_reservations = SchoolUser.objects.annotate(
        reservation_count=Count('reservation', distinct=True)
    ).filter(reservation_count__gt=0).count()
    departments_with_reservations = Department.objects.filter(
        schooluser__reservation__isnull=False
    ).annotate(reservation_count=Count('schooluser__reservation', distinct=True)).count()
    total_students = Reservation.objects.exclude(status='denied').aggregate(
        total_students=Sum(Case(
            When(student_number__isnull=False, then=Cast('student_number', IntegerField())),
            default=Value(0),
            output_field=IntegerField()
        ))
    )
    context.update({
        'res_num': res_num, 
        'school_users_with_reservations': school_users_with_reservations, 
        'departments_with_reservations': departments_with_reservations,
        'total_students': total_students['total_students'],
    })

    return render(request, 'reservations/statistics_all_years.html', context)

def reservationsPerSchoolYearTotal(request):

    school_years = SchoolYear.objects.all().order_by('start_date')
    school_years_values = SchoolYear.objects.all().order_by('start_date').values('name')

    #fill in school years
    school_years_names = []

    for i in range(len(school_years_values)):
        school_years_names.append(school_years_values[i]['name'])

    #fill in number of reservations per school year
    res_per_sch_year = []

    for i in range(len(school_years)):
        res_per_sch_year.append(Reservation.objects.filter(reservation_period__schoolYear=school_years[i]).count())

    volumes_per_sch_year = []
    for i in range(len(school_years_names)):
        volumes_per_sch_year.append({school_years_names[i]:res_per_sch_year[i]})

    return JsonResponse(volumes_per_sch_year, safe=False)

def reservationsPerResPeriodTotal(request):

    res_per = ReservationPeriod.objects.all().order_by('start_date')
    res_per_values = ReservationPeriod.objects.all().order_by('start_date').values('name')

    #fill in reservation periods
    res_periods = []

    for i in range(len(res_per_values)):
        res_periods.append(res_per_values[i]['name'])

    #fill in number of reservations per reservation period
    res_per_res_period = []

    for i in range(len(res_periods)):
        res_per_res_period.append(Reservation.objects.filter(reservation_period=res_per[i]).exclude(status='denied').count())

    volumes_per_res_period = []
    for i in range(len(res_periods)):
        volumes_per_res_period.append({res_periods[i]:res_per_res_period[i]})

    return JsonResponse(volumes_per_res_period, safe=False)

def studentsPerSchoolYearTotal(request):

    school_years = SchoolYear.objects.all().order_by('start_date')
    school_years_values = SchoolYear.objects.all().order_by('start_date').values('name')

    #fill in school years
    school_years_names = []

    for i in range(len(school_years_values)):
        school_years_names.append(school_years_values[i]['name'])

    #fill in student number
    stud_num=[]

    for i in range(len(school_years)):
        students = Reservation.objects.filter(reservation_period__schoolYear=school_years[i]).exclude(status='denied').aggregate(total_students=Sum(Cast('student_number', IntegerField())))
        stud_num.append(students['total_students'])

    #json dict
    students_per_year=[]
    for i in range(len(school_years_names)):
        students_per_year.append({school_years_names[i]:stud_num[i]})

    return JsonResponse(students_per_year, safe=False)

def studentsPerResPeriodTotal(request):

    res_per = ReservationPeriod.objects.all().order_by('start_date')
    res_per_values = ReservationPeriod.objects.all().order_by('start_date').values('name')

    #fill in reservation periods
    res_periods = []

    for i in range(len(res_per_values)):
        res_periods.append(res_per_values[i]['name'])

    #fill in student number
    stud_num=[]

    for i in range(len(res_periods)):
        students = Reservation.objects.filter(reservation_period=res_per[i]).exclude(status='denied').aggregate(total_students=Sum(Cast('student_number', IntegerField())))
        stud_num.append(students['total_students'])

    #json dict
    students_per_res_period=[]
    for i in range(len(res_periods)):
        students_per_res_period.append({res_periods[i]:stud_num[i]})

    return JsonResponse(students_per_res_period, safe=False)

@ login_required
@user_passes_test(lambda u: u.is_superuser)   
def statistics_period_selection(request):

    form = ReservationCalendarByDateForm()
    context = {}

    selected_reservation_period_id = request.GET.get('reservation_period')
    selected_school_year_id = request.GET.get('school_year')

    # Check if the Filter button is clicked
    if request.GET.get('filter') == '1' and selected_reservation_period_id:
        # Reset selected values
        form = ReservationCalendarByDateForm()
        return redirect('reservations:statistics_per_period', reservation_id=selected_reservation_period_id)
    
    if request.GET.get('filter') == '1' and selected_reservation_period_id == '' and selected_school_year_id:
        # Reset selected values
        form = ReservationCalendarByDateForm()
        return redirect('reservations:statistics_per_year', schoolYear_id=selected_school_year_id)

    if request.GET.get('filter') == '1' and selected_reservation_period_id == '' and selected_school_year_id == '':
        # Reset selected values
        form = ReservationCalendarByDateForm()
        return redirect('reservations:statistics_all_years')

    if request.GET.get('filter') == '2':
        form = ReservationCalendarByDateForm()

    context.update({
        'form': form
    })

    return render(request, 'reservations/statistics_period_selection.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reservation_details(request, reservation_id):

    reservation = get_object_or_404(Reservation, id=reservation_id)
    reservation_date = reservation.reservation_date
    schoolUser = reservation.schoolUser
    timeslot = reservation.timeslot
    teacher_number = reservation.teacher_number
    student_number = reservation.student_number
    amea = reservation.amea
    terms_accepted = reservation.terms_accepted
    status = reservation.status
    is_performed = reservation.is_performed
    created_at = reservation.created_at

    context = {'reservation': reservation,
            'reservation_date': reservation_date,
            'schoolUser': schoolUser,
            'timeslot': timeslot,
            'teacher_number': teacher_number,
            'student_number': student_number,
            'amea': amea,
            'terms_accepted': terms_accepted,
            'status': status,
            'is_performed': is_performed,
            'created_at': created_at,
    }

    return render(request, 'reservations/reservation_screener.html', context)

class ReservationPDFView(View):
    template_name = 'reservations/reservation_details.html'  # Create an HTML template for the details

    def get(self, request, reservation_id, *args, **kwargs):
        reservation = Reservation.objects.get(pk=reservation_id)

        # Render the HTML template with the reservation details
        template = get_template(self.template_name)
        html = template.render({'reservation': reservation})

        # Create a PDF file
        response = HttpResponse(content_type='application/pdf')
        #response['Content-Disposition'] = f'filename={reservation_id}_reservation_details.pdf'
        response['Content-Disposition'] = f'attachment; filename={reservation.id}_reservation_details.pdf'

        # Generate the PDF
        pisa_status = pisa.CreatePDF(html, dest=response)
        if pisa_status.err:
            return HttpResponse('We had some errors <pre>' + html + '</pre>')

        return response

@login_required
@user_passes_test(lambda u: u.is_superuser)
def reservations_created_by_admin(request):

    reservations_created_by_admin = Reservation.objects.filter(schoolUser__creator__is_superuser=True).order_by('-created_at', 'schoolUser__school__name')

    context = {
        'reservations_created_by_admin': reservations_created_by_admin,
        'reservations_created_by_admin_num': len(reservations_created_by_admin),
    }

    return render(request, 'reservations/reservations_created_by_admin.html', context)