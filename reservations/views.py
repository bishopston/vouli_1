from django.shortcuts import render, redirect, HttpResponseRedirect, get_object_or_404
from django.http import Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.forms import formset_factory
from django.core.serializers import serialize
from django.http import JsonResponse
from django.db.models import Q
from django.contrib import messages
from django.core.mail import send_mail
from .models import Day, ReservationPeriod, Timeslot, DayTime, Reservation, ReservationWindow, ExceptionalRule, SchoolYear
from schools.models import SchoolUser
from .forms import ReservationForm, BaseReservationFormSet, ReservationUpdateForm
from .utils import get_occupied_daytimes, get_allowed_daytimes, get_occupied_exceptional_daytimes, get_allowed_exceptional_daytimes, calculate_availability_percentage
from datetime import timedelta
#from calendar import monthrange
import datetime
from datetime import datetime as dt
import pytz
from datetime import datetime, date


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
        return HttpResponseRedirect(request.path_info)

    return render(request, 'reservations/add_timeslots.html', {'reservation_period': reservation_period, 'qs_days': qs_days, 'qs_slots': qs_slots})

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
    
@login_required
def calendar_month(request, reservation_period_id, school_user_id, year=None, month=None):
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
        start_date = timezone.now()

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

    return render(request, 'reservations/calendar_month_3.html', context)

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
    #query user's reservations
    my_reservations = Reservation.objects.filter(schoolUser__creator=request.user).order_by('-reservation_date__date', 'timeslot__dayTime__slot')

    #query current school year
    current_school_year = SchoolYear.objects.filter(start_date__lte=datetime.now(), end_date__gte=datetime.now()).first()
    if current_school_year:   
        # Use Q objects to handle the OR condition for start and end dates
        query = Q(schoolUser__creator=request.user) & Q(reservation_period__schoolYear=current_school_year)
        # Filter reservations based on the current school year and the user
        my_reservations_current_year_number = len(Reservation.objects.filter(query).exclude(status='denied'))
    else:
        my_reservations_current_year_number = 0

    #query closest available reservation period whose start date hasn't come yet and res window has not finished yet - closest_available_res_period[0]
    q = ReservationPeriod.objects.filter(is_available=True).filter(start_date__gte=dt.now()).filter(reservationwindow__end_date__gte=dt.now(pytz.utc))
    
    #ensure that admin has made a ReservationPeriod available
    if len(q) > 0:
    
        dates = q.values('start_date').order_by('start_date')
        closest_available_res_period = q.filter(start_date=dates[0]['start_date'])

        try:
            #ensure that user has created a school
            my_school = SchoolUser.objects.filter(creator=request.user)[0]#.school.name

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

                return render(request, 'reservations/myreservations.html', context)

            else:

                context = {'my_reservations': my_reservations,
                        'my_reservations_current_year_number': my_reservations_current_year_number,
                        'my_school': my_school,
                }

                return render(request, 'reservations/myreservations.html', context)               

        except (IndexError, SchoolUser.DoesNotExist):
            return render(request, 'reservations/myreservations.html')

    else:

        try:
            my_school = SchoolUser.objects.filter(creator=request.user)[0].school.name

            context = {'my_reservations': my_reservations,
                    'my_reservations_current_year_number': my_reservations_current_year_number,
                    'my_school': my_school,
            }

            return render(request, 'reservations/myreservations.html', context)

        except (IndexError, SchoolUser.DoesNotExist):
            return render(request, 'reservations/myreservations.html')


@login_required
def make_reservation(request, reservation_period_id, school_user_id):
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

            #query current school year
            current_school_year = SchoolYear.objects.filter(start_date__lte=datetime.now(), end_date__gte=datetime.now()).first()
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
                context['different_selected_date_violation_error'] = 'Δικαιούστε να καταχωρίσετε αίτημα επίσκεψης σε μία μόνο ημερομηνία εντός του τρέχοντος σχολικού έτους.'
            else:
                if submitted_forms_count <= max_additional_reservations:
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
                    return HttpResponseRedirect(reverse('reservations:my_reservations'))
                
                else:
                    context['max_allowed_violation_error'] = 'Δικαιούστε να καταχωρίσετε αίτημα επίσκεψης για έως τρεις ομάδες μαθητών/τριών σε μία μόνο ημερομηνία.'

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

    return render(request, 'reservations/reservation2.html', context)


@login_required
def preview_reservation(request, reservation_period_id, school_user_id):

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
        #print(time_str)
        #day_str = date  # Assuming date is passed as a query parameter
        selected_date_format = datetime.strptime(date, "%Y-%m-%d")
        #print(selected_date_format)
        day_of_week = day_of_week_mapping[selected_date_format.strftime('%A')]
        #print(day_of_week)
        day_time = DayTime.objects.get(day=day_of_week, slot=time_str)
        #print(day_time)
        form_data['timeslot'] = Timeslot.objects.filter(dayTime=day_time).first()
        #print(form_data['timeslot'])
    
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

            #query current school year
            current_school_year = SchoolYear.objects.filter(start_date__lte=datetime.now(), end_date__gte=datetime.now()).first()
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
                        #print(timeslot_instance)
                        timeslot_id = timeslot_instance.id
                        #print(timeslot_id)
                        Reservation.objects.create(timeslot_id=timeslot_id, 
                                                reservation_period=ReservationPeriod.objects.get(id=reservation_period_id), 
                                                schoolUser=SchoolUser.objects.get(id=school_user_id),
                                                reservation_date=Day.objects.get(id=selected_date_id),
                                                updated_by=request.user,
                                                **form_data)

                    # Clear the session data
                    request.session.pop('formset_data', None)

                    # Redirect to a success page or another view
                    return HttpResponseRedirect(reverse('reservations:my_reservations'))
                
                else:
                    preview_max_allowed_violation_error = 'Δικαιούστε να καταχωρίσετε αίτημα επίσκεψης για έως τρεις ομάδες μαθητών/τριών σε μία μόνο ημερομηνία.'
                    return redirect(redirect_url + f'&preview_max_allowed_violation_error={preview_max_allowed_violation_error}')

    return render(request, 'reservations/preview_reservation3.html', {'formset': formset,
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
        start_date = timezone.now()

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

    if delete_reservation.schoolUser.creator != request.user:
        raise Http404("Αδυναμία πρόσβασης")
    else:
        if request.method == 'POST':    
            if delete_reservation.status == 'pending':
                delete_reservation.delete()                    
                return redirect('reservations:my_reservations')  
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

    available_res_periods = ReservationPeriod.objects.filter(is_available=True)
    context = {}

    if len(available_res_periods) > 0:
        dates = available_res_periods.values('start_date').order_by('start_date')
        closest_available_res_period = available_res_periods.filter(start_date=dates[0]['start_date'])
        candidate_reservations = Reservation.objects.filter(reservation_period=closest_available_res_period[0]).order_by('-created_at', 'timeslot__dayTime__slot')
        context['closest_available_res_period'] = closest_available_res_period[0]
        context['candidate_reservations'] = candidate_reservations
    else:
        context['no_available_res_period'] = 'Δεν έχετε δηλώσει καμία περίοδο επισκέψεων ως διαθέσιμη για κρατήσεις.'

    if request.method == 'POST':
        reservation_ids = request.POST.getlist('reservation_ids')
        action = request.POST.get('action')
        #print('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        #print(action)

        reservations = Reservation.objects.filter(id__in=reservation_ids)

        if action == 'approve':
            reservations.update(status='approved', updated_at=timezone.now())
            #context['approve_message'] = 'Εγκρίνατε με επιτυχία τις επιλεγμένες κρατήσεις.'
            messages.success(request, 'Εγκρίνατε με επιτυχία τις επιλεγμένες κρατήσεις.')
            # Send a consolidated email to each user
            send_consolidated_reservation_emails(reservations)
        elif action == 'deny':
            reservations.update(status='denied', updated_at=timezone.now())
            #context['deny_message'] = 'Απορρίψατε με επιτυχία τις επιλεγμένες κρατήσεις.'
            messages.success(request, 'Απορρίψατε με επιτυχία τις επιλεγμένες κρατήσεις.')
            # Send a consolidated email to each user
            send_consolidated_reservation_emails(reservations)
        elif action == 'performed':
            reservations.update(is_performed=True, updated_at=timezone.now())
            #context['performed_message'] = 'Αλλάξατε με επιτυχία την κατάσταση των επιλεγμένων κρατήσεων σε πραγματοποιημένες.'
            messages.success(request, 'Αλλάξατε με επιτυχία την κατάσταση των επιλεγμένων κρατήσεων σε πραγματοποιημένες.')
        elif action == 'nonperformed':
            reservations.update(is_performed=False, updated_at=timezone.now())
            #context['nonperformed_message'] = 'Αλλάξατε με επιτυχία την κατάσταση των επιλεγμένων κρατήσεων σε μη πραγματοποιημένες.'
            messages.success(request, 'Αλλάξατε με επιτυχία την κατάσταση των επιλεγμένων κρατήσεων σε μη πραγματοποιημένες.')

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
    subject = 'Your Reservations Status'
    message = 'Your reservations have been processed.\n'

    # Add details of each reservation to the email message
    for reservation in reservations:
        message += f'Reservation ID: {reservation.id}, Date: {reservation.reservation_date}, Status: {reservation.get_status_display()}\n'

    # Send the email
    send_mail(
        subject,
        message,
        'admin@parliament.foundation',
        [user.email], 
        fail_silently=False,
    )

# @ login_required
# @user_passes_test(lambda u: u.is_superuser)
# def update_reservation_admin(request, reservation_id):
#     update_reservation = get_object_or_404(Reservation, id=reservation_id) 
#     reservationUpdateForm = ReservationUpdateForm(instance=update_reservation)

#     if update_reservation.schoolUser.creator != request.user:
#         raise Http404("Αδυναμία πρόσβασης")
#     else:
#         if request.method == 'POST':
#             reservationUpdateForm = ReservationUpdateForm(request.POST, instance=update_reservation)
#             if reservationUpdateForm.is_valid():
#                 reservationUpdateForm.save()
#                 return redirect(reverse('reservations:my_reservations'))

#     return render(request, 'reservations/update_reservation.html', {'update_reservation':update_reservation, 
#                                                                     'reservationUpdateForm': reservationUpdateForm,
#                                                                     'schoolUser': schoolUser,
#                                                                     'reservationDateName': update_reservation.reservation_date.date.strftime("%A"),
#                                                                     'reservationDateDay': update_reservation.reservation_date.date.strftime("%d"),
#                                                                     'reservationDateMonth': update_reservation.reservation_date.date.strftime("%B"),
#                                                                     'reservationDateYear': update_reservation.reservation_date.date.year,                                                                    
#                                                                     })
