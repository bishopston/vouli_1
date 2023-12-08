from django.shortcuts import render, redirect, HttpResponseRedirect, get_object_or_404
from django.http import Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.forms import formset_factory
from django.core.exceptions import ValidationError
from django.core.serializers import serialize
from django.http import JsonResponse
from django.db.models import Q
from django.http import QueryDict
from .models import Day, ReservationPeriod, Timeslot, DayTime, Reservation, ReservationWindow, ExceptionalRule, SchoolYear
from schools.models import SchoolUser
from .forms import ReservationForm, BaseReservationFormSet, ExceptionalRuleForm
from .utils import get_occupied_daytimes, get_allowed_daytimes, get_occupied_exceptional_daytimes, get_allowed_exceptional_daytimes, calculate_availability_percentage
from datetime import timedelta
#from calendar import monthrange
import datetime
from datetime import datetime as dt
import pytz
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import calendar
import json

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_timeslots(request, reservation_period_id):

    # Pass the days and hours to the template
    #days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    #hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00']

    #fill in days for frontend
    #qs_days = DayTime.objects.all().values('day').order_by('day').distinct()
    qs_days = DayTime.objects.all().filter(slot='09:00:00').order_by('day').distinct()
    # days = []
    # for i in range(len(qs_days)):
    #     days.append(qs_days[i]['day'])

    #fill in hours for frontend
    #qs_slots = DayTime.objects.all().values('slot').order_by('slot').distinct()
    qs_slots = DayTime.objects.all().filter(day='a').order_by('slot').distinct()
    # hours = []
    # for i in range(len(qs_slots)):
    #     hours.append(qs_slots[i]['slot'])

    reservation_period = ReservationPeriod.objects.get(id=reservation_period_id)
    if request.method == 'POST':
        timeslots = request.POST.getlist('timeslots')

        for timeslot in timeslots:
            #day = timeslot.day
            #hour = timeslot.hour
            # Create Timeslot objects based on the selected checkboxes
            #print(f"Day: {day}, Hour: {hour}")
            #print(timeslot)
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


# def add_exceptional_rule(request):
#     selected_date = request.GET.get('date')
#     print(selected_date)

#     # Get the selected day and corresponding DayTime instances
#     selected_day = Day.objects.get(date=selected_date)
    # day_of_week_mapping = {
    #     'Monday': 'a',
    #     'Tuesday': 'b',
    #     'Wednesday': 'c',
    #     'Thursday': 'd',
    #     'Friday': 'e',
    #     'Saturday': 'f',
    #     'Sunday': 'g',
    # }
#     selected_day_of_week = day_of_week_mapping[selected_day.date.strftime('%A')]

#     # Find the corresponding DayTime instances for the determined day
#     available_daytimes = DayTime.objects.filter(day=selected_day_of_week)

#     if request.method == 'POST':
#         daytimes = request.POST.getlist('daytimes')
#         selected_date = request.POST.get('selected_date')
#         selected_day = Day.objects.get(date=selected_date)
#         # day_of_week_mapping = {
#         #     'Monday': 'a',
#         #     'Tuesday': 'b',
#         #     'Wednesday': 'c',
#         #     'Thursday': 'd',
#         #     'Friday': 'e',
#         #     'Saturday': 'f',
#         #     'Sunday': 'g',
#         # }
#         # selected_day_of_week = day_of_week_mapping[selected_day.date.strftime('%A')]

#         for daytime in daytimes:
                        
#             #print(f"Day: {day}, Hour: {hour}")
#             print(selected_day)
#             submitted_daytimes = ExceptionalRule.objects.filter(date=selected_day, timeslot=daytime)

#             if submitted_daytimes.exists():
#                 return render(request, 'reservations/add_exceptional_rule.html', {'selected_date': selected_date, 'available_daytimes': available_daytimes, 'error_message': 'Έχετε προβεί σε διπλοεγγραφή χρονοθυρίδας. Η ενέργεια ακυρώθηκε.'})

#             else:
#                 # Create ExceptionalRule objects based on the selected checkboxes
#                 ExceptionalRule.objects.create(
#                     date=selected_day,
#                     timeslot=daytime
#                 )
#         return HttpResponseRedirect(request.path_info)

#     context = {
#         'selected_date': selected_date,
#         'available_daytimes': available_daytimes,
#     }

#     return render(request, 'reservations/add_exceptional_rule.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_exceptional_rule(request):

    # If the form was not submitted via POST, handle accordingly
    res_period_id = request.GET.get('reservationPeriodId') or request.POST.get('res_period_id')
    selected_date = request.GET.get('date') or request.POST.get('selected_date')
    error = request.GET.get('error', None)
    print(error)

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
                #messages.error(request, 'Έχετε προβεί σε διπλοεγγραφή χρονοθυρίδας. Η ενέργεια ακυρώθηκε.')
                #return render(request, 'reservations/add_exceptional_rule.html', {'selected_date': selected_date, 'available_daytimes': available_daytimes, 'error_message': error_message})
                #return redirect(reverse('reservations:add_exceptional_rule'))
            
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

    # selected_day = Day.objects.get(date=selected_date)

    # created_exceptional_rules = ExceptionalRule.objects.filter(date=selected_day)

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
    
# def make_reservation(request, reservation_period_id):

#     reservation_period = ReservationPeriod.objects.get(id=reservation_period_id)

#     if request.method == 'POST':
#         form = ReservationForm(request.POST)
#         if form.is_valid():
#             reservation_date = form.cleaned_data['reservation_date']
#             timeslot_id = form.cleaned_data['timeslot']
#             timeslot = get_object_or_404(Timeslot, id=timeslot_id)

#             # Check if the selected day is not a vacation
#             day_is_vacation = Day.objects.filter(date=reservation_date, is_vacation=True).exists()
            
#             # Check if the reservation period is available
#             reservation_period_is_available = reservation_period.is_available

#             # Check if the selected timeslot is allowed for reservation
#             if not day_is_vacation and reservation_period_is_available and timeslot.is_reservation_allowed:
#                 # Create the reservation
#                 reservation = Reservation.objects.create(
#                     reservation_date=reservation_date,
#                     timeslot=timeslot,
#                     user=request.user,  # Assuming you have a user associated with the reservation
#                     reservation_period=reservation_period,
#                     status='pending',
#                     is_performed=False
#                 )

#                 messages.success(request, 'Reservation created successfully.')
#             elif day_is_vacation:
#                 messages.error(request, 'Selected day is a vacation and not available for reservations.')
#             elif not reservation_period_is_available:
#                 messages.error(request, 'Reservation period is not available for reservations.')
#             elif not timeslot.is_reservation_allowed:
#                 messages.error(request, 'Selected timeslot is not available for reservation.')
#         else:
#             messages.error(request, 'Invalid form submission. Please check your input.')

#     return render(request, 'your_template.html', {'form': ReservationForm(), 'reservation_period': reservation_period})

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

# def get_month_days(year, month, res_period_id):
#     # Implement your logic to retrieve days for the given month and year
#     # For simplicity, assuming a Day model with a 'date' field
#     res_period = ReservationPeriod.objects.get(pk=res_period_id)
#     days = Day.objects.filter(date__gte=res_period.start_date, date__lte=res_period.end_date).filter(date__year=year, date__month=month)

#     # # Find the weekday of the first day of the month
#     # first_day_weekday = days[0].date.weekday()

#     # # Rotate days to start the weeks with the correct day
#     # days = list(days[7 - first_day_weekday:]) + list(days[:7 - first_day_weekday])

#     # # Find the weekday of the first day of the month
#     # first_day_weekday = calendar.monthrange(year, month)[0]

#     # # Rotate days to start the weeks with the correct day
#     # days = list(days[7 - first_day_weekday:]) + list(days[:7 - first_day_weekday])

#     # Find the weekday of the first day of the month and the number of days in the month
#     # first_day_weekday, num_days_in_month = calendar.monthrange(year, month)

#     # # Generate a list of days for the month
#     # days = [date(year, month, day) for day in range(1, num_days_in_month + 1)]

#     # # Pad the beginning of the list with days from the previous week
#     # # days = [date(year, month, 1 - first_day_weekday) - timedelta(days=1)] * first_day_weekday + days
#     # days = [date(year, month, max(1, 1 - first_day_weekday)) - timedelta(days=1)] * max(0, first_day_weekday) + days


#     # # Find the weekday of the first day of the month and the number of days in the month
#     # first_day_weekday, num_days_in_month = calendar.monthrange(year, month)

#     # # Generate a list of days for the month
#     # days = [date(year, month, day) for day in range(1, num_days_in_month + 1)]

#     # # Pad the beginning of the list with days from the previous week
#     # days = [date(year, month, max(1, 1 - first_day_weekday)) - timedelta(days=1)] * max(0, first_day_weekday) + days

#     # # Split the list into weeks
#     # weeks = [days[i:i + 7] for i in range(0, len(days), 7)]

#     # return weeks


#     return chunk_days(days)

# def get_month_days(year, month, res_period_id):
#     # Assuming a Day model with a 'date' field
#     res_period = ReservationPeriod.objects.get(pk=res_period_id)

#     # Fetch the Day objects for the given month and year
#     days = Day.objects.filter(
#         Q(date__year=year, date__month=month) &
#         Q(date__gte=res_period.start_date, date__lte=res_period.end_date)
#     ).order_by('date')

#     # Pad the beginning of the list with days from the previous week
#     first_day_weekday = days[0].date.weekday()
#     days = [days[0].date - timedelta(days=first_day_weekday)] * first_day_weekday + list(days)

#     # Split the list into weeks
#     weeks = [days[i:i + 7] for i in range(0, len(days), 7)]

#     return weeks

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
    my_reservations = Reservation.objects.filter(schoolUser__creator=request.user)
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
                        'next_available_res_period': closest_available_res_period[0],
                        'next_available_res_period_start_date': closest_available_res_period[0].start_date,
                        'next_available_res_period_end_date': closest_available_res_period[0].end_date,
                        'reservation_allowed': closest_available_res_period[0].reservationwindow_set.first().is_reservation_allowed(),
                        'my_school': my_school,
                }

                return render(request, 'reservations/myreservations.html', context)

            else:

                context = {'my_reservations': my_reservations,
                        'my_school': my_school,
                }

                return render(request, 'reservations/myreservations.html', context)               

        except (IndexError, SchoolUser.DoesNotExist):
            return render(request, 'reservations/myreservations.html')

    else:

        try:
            my_school = SchoolUser.objects.filter(creator=request.user)[0].school.name

            context = {'my_reservations': my_reservations,
                    'my_school': my_school,
            }

            return render(request, 'reservations/myreservations.html', context)

        except (IndexError, SchoolUser.DoesNotExist):
            return render(request, 'reservations/myreservations.html')

# @login_required
# def make_reservation(request, reservation_period_id, school_user_id):
#     schoolUser = SchoolUser.objects.get(pk=school_user_id)
#     res_period = get_object_or_404(ReservationPeriod, pk=reservation_period_id)
#     date = request.GET.get('date')

#     #get week day name
#     selected_date = datetime.strptime(date, "%Y-%m-%d")
#     selected_calendar_date = Day.objects.get(date=selected_date)
#     selected_calendar_date_name = selected_calendar_date.date.strftime("%A")

#     #get date string
#     #selected_calendar_date_string = selected_calendar_date.date.strftime("%d %B %Y")
#     selected_calendar_date_day = selected_calendar_date.date.strftime("%d")
#     selected_calendar_date_month = selected_calendar_date.date.strftime("%B")
#     selected_calendar_date_year = selected_calendar_date.date.strftime("%Y")

#     if len(ExceptionalRule.objects.filter(date = selected_calendar_date)) > 0:

#         allowed_timeslots = get_allowed_exceptional_daytimes(date, reservation_period_id)
#         occupied_timeslots = get_occupied_exceptional_daytimes(date, reservation_period_id)

#     else:

#         allowed_timeslots = get_allowed_daytimes(date, reservation_period_id)
#         occupied_timeslots = get_occupied_daytimes(date, reservation_period_id)

#     non_occupied_timeslots = allowed_timeslots.exclude(id__in=occupied_timeslots)
#     non_occupied_timeslots_count = len(non_occupied_timeslots)

#     # form = ReservationForm(
#     #     reservation_period=res_period,
#     #     selected_date=date,
#     #     initial={'reservation_date': date, 'reservation_period': res_period.id}
#     # )

#     #formset = ReservationFormSet(initial=[{'reservation_date': date, 'reservation_period': res_period.id}] * 3)

#     # if request.method == 'POST':
#     #     form = ReservationForm(request.POST)
#     #     if form.is_valid():
#     #         my_reservation = Reservation(
#     #             schoolUser = schoolUser,
#     #             reservation_date = selected_calendar_date,
#     #             timeslot = form.cleaned_data["timeslot"],
#     #             teacher_number = form.cleaned_data["teacher_number"],
#     #             student_number = form.cleaned_data["student_number"],
#     #             amea = form.cleaned_data["amea"],
#     #             terms_accepted = form.cleaned_data["terms_accepted"],
#     #             reservation_period = res_period,
#     #         )
#     #         my_reservation.save()
#     #         return HttpResponseRedirect(reverse('reservations:my_reservations'))
#     # else:
#     # #     form = ReservationForm(reservation_period=res_period_id, initial={'reservation_date': date})
#     #     form = ReservationForm(
#     #         reservation_period=res_period,
#     #         selected_date=date,
#     #         initial={'reservation_date': date, 'reservation_period': res_period.id}
#     #     )

#     #ReservationFormSet = formset_factory(extra=3, formset=BaseReservationFormSet)
#     context = {} 

#     ReservationFormSet = formset_factory(ReservationForm, extra=3, max_num=3, formset=BaseReservationFormSet)

#     if request.method == 'POST':
#         formset = ReservationFormSet(request.POST, reservation_period=res_period, selected_date=date)
#         if formset.is_valid():
#             for form in formset:
#                 # process each form in the formset
#                 if form.cleaned_data.get('timeslot'):
#                     my_reservation = Reservation(
#                         schoolUser = schoolUser,
#                         reservation_date = selected_calendar_date,
#                         timeslot = form.cleaned_data["timeslot"],
#                         teacher_number = form.cleaned_data["teacher_number"],
#                         student_number = form.cleaned_data["student_number"],
#                         amea = form.cleaned_data["amea"],
#                         terms_accepted = form.cleaned_data["terms_accepted"],
#                         reservation_period = res_period
#                     )
#                     my_reservation.save()

#             return HttpResponseRedirect(reverse('reservations:my_reservations'))
        
#         else:
#             # Formset is not valid, include it in the context
#             context['formset'] = formset
#             # Include specific error messages in the context
#             context['timeslot_error'] = any(formset.errors) and formset.errors[0].get('timeslot')
#             context['terms_accepted_error'] = any(formset.errors) and formset.errors[0].get('terms_accepted')

#             #return render(request, 'reservations/reservation.html', context)
    
#     else:
#         formset = ReservationFormSet(reservation_period=res_period, selected_date=date)
        

#     # context = {
#     #     'res_period': res_period,
#     #     #'res_period_id': res_period.id,
#     #     'schoolUser': schoolUser,
#     #     'date': date,
#     #     'week_day': selected_calendar_date_name,
#     #     'selected_calendar_date_day': selected_calendar_date_day,
#     #     'selected_calendar_date_month': selected_calendar_date_month,
#     #     'selected_calendar_date_year': selected_calendar_date_year,
#     #     'allowed_timeslots': allowed_timeslots,
#     #     'occupied_timeslots': occupied_timeslots,
#     #     'non_occupied_timeslots': non_occupied_timeslots,
#     #     'non_occupied_timeslots_count': non_occupied_timeslots_count,
#     #     #'form': form,
#     #     'formset': formset,
#     # }

#     context.update({
#         'res_period': res_period,
#         'schoolUser': schoolUser,
#         'date': date,
#         'week_day': selected_calendar_date_name,
#         'selected_calendar_date_day': selected_calendar_date_day,
#         'selected_calendar_date_month': selected_calendar_date_month,
#         'selected_calendar_date_year': selected_calendar_date_year,
#         'allowed_timeslots': allowed_timeslots,
#         'occupied_timeslots': occupied_timeslots,
#         'non_occupied_timeslots': non_occupied_timeslots,
#         'non_occupied_timeslots_count': non_occupied_timeslots_count,
#         'formset': formset,
#         'exceptional_rules': ExceptionalRule.objects.filter(date = selected_calendar_date),
#     })

#     return render(request, 'reservations/reservation.html', context)


@login_required
def make_reservation(request, reservation_period_id, school_user_id):
    schoolUser = SchoolUser.objects.get(pk=school_user_id)
    res_period = get_object_or_404(ReservationPeriod, pk=reservation_period_id)
    date = request.GET.get('date')

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

        # if request.POST.get('preview') == '1':
        #     # If the preview button is clicked, store formset data in the session
        #     # request.session['formset_data'] = request.POST
        #     # return redirect('reservations:preview_reservation', reservation_period_id=reservation_period_id, school_user_id=school_user_id)
        #     #selected_date = request.GET.get('date', None)

        #     formset_data = {}
        #     for key, value in request.POST.items():
        #         if key.startswith('form-'):
        #             if 'timeslot' in key:
        #                 try:
        #                     timeslot_id = int(value)
        #                     print(timeslot_id)
        #                     timeslot = Timeslot.objects.get(pk=timeslot_id)
        #                     formset_data[key] = timeslot.dayTime.slot.strftime("%H:%M")  # Assuming display_time is the attribute you want to show
        #                 except (ValueError, Timeslot.DoesNotExist):
        #                     # Handle the case where the value is not a valid timeslot ID
        #                     formset_data[key] = value
        #             else:
        #                 formset_data[key] = value


        #     request.session['formset_data'] = formset_data

        #     # Redirect to the preview page
        #     # preview_url = reverse('reservations:preview_reservation', args=(reservation_period_id, school_user_id,))
        #     # return HttpResponseRedirect(preview_url + f'?date={date}')

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
            # Process and save the reservations
            for form in formset:
                if form.cleaned_data.get('timeslot'):
                    my_reservation = Reservation(
                        schoolUser=schoolUser,
                        reservation_date=selected_calendar_date,
                        timeslot=form.cleaned_data["timeslot"],
                        teacher_number=form.cleaned_data["teacher_number"],
                        student_number=form.cleaned_data["student_number"],
                        amea=form.cleaned_data["amea"],
                        terms_accepted=form.cleaned_data["terms_accepted"],
                        reservation_period=res_period
                    )
                    my_reservation.save()

            return HttpResponseRedirect(reverse('reservations:my_reservations'))
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
        'schoolUser': schoolUser,
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
    })

    return render(request, 'reservations/reservation2.html', context)


# def preview_reservation(request, reservation_period_id, school_user_id):

#     date = request.GET.get('date')
#     # Retrieve formset data from the session

#     formset_data = request.session.get('formset_data', None)

#     #print("Formset Data:", formset_data)

#     if formset_data:
        
#         # Create a list of form prefixes to exclude in the template
#         form_prefixes = ['form-TOTAL_FORMS', 'form-INITIAL_FORMS', 'form-MIN_NUM_FORMS', 'form-MAX_NUM_FORMS']
#         #field_names = [key for key in formset_data.keys() if key not in ['form-TOTAL_FORMS', 'form-INITIAL_FORMS', 'form-MIN_NUM_FORMS', 'form-MAX_NUM_FORMS']]

#         # # Filter out unnecessary keys
#         # filtered_data = {key: formset_querydict.getlist(key) for key in formset_querydict.keys() if key and not key.startswith('form-') and key not in ['csrfmiddlewaretoken', 'preview']}
                
#         # Render the preview page with the formset data
#         return render(request, 'reservations/preview_reservation.html', {'formset_data': formset_data, 
#                                                                          'reservation_period_id': reservation_period_id,
#                                                                          'school_user_id': school_user_id,
#                                                                          'form_prefixes': form_prefixes,
#                                                                          'date': date
#                                                                          })
#     if request.method == 'POST':

#         print(request.POST.items())
#         print("giouxou")

#         return redirect('reservations:make_reservation', reservation_period_id=reservation_period_id, school_user_id=school_user_id)
#         # return render(request, 'reservations/preview_reservation.html', {'formset_data': formset_data, 
#         #                                                             'reservation_period_id': reservation_period_id,
#         #                                                             'school_user_id': school_user_id,
#         #                                                             'form_prefixes': form_prefixes,
#         #                                                             'date': date
#         #                                                             })
    
#     else:
#         # If there is no formset data, redirect to the reservation page
#         return redirect('reservations:make_reservation', reservation_period_id=reservation_period_id, school_user_id=school_user_id)

# def preview_reservation(request, reservation_period_id, school_user_id):
#     # Retrieve formset data from the session
#     formset_data = request.session.get('formset_data', None)

#     # Add the following line to handle the formset
#     ReservationFormSet = formset_factory(ReservationForm, extra=3, max_num=3, formset=BaseReservationFormSet)
#     formset = ReservationFormSet(data=formset_data) if formset_data else None

#     #print(formset)
#     schoolUser = SchoolUser.objects.get(pk=school_user_id)
#     res_period = get_object_or_404(ReservationPeriod, pk=reservation_period_id)

#     date = request.GET.get('date')

#     #get week day name
#     selected_date = datetime.strptime(date, "%Y-%m-%d")
#     selected_calendar_date = Day.objects.get(date=selected_date)

#     if request.method == 'POST':
#         formset = ReservationFormSet(request.POST, reservation_period=res_period, selected_date=date)

#         if formset.is_valid():
#             # Process and save the reservations
#             for form in formset:
#                 if form.cleaned_data.get('timeslot'):
#                     my_reservation = Reservation(
#                         schoolUser=schoolUser,
#                         reservation_date=selected_calendar_date,
#                         timeslot=form.cleaned_data["timeslot"],
#                         teacher_number=form.cleaned_data["teacher_number"],
#                         student_number=form.cleaned_data["student_number"],
#                         amea=form.cleaned_data["amea"],
#                         terms_accepted=form.cleaned_data["terms_accepted"],
#                         reservation_period=res_period
#                     )
#                     my_reservation.save()

#             # Redirect to the confirmation page or any other page
#             return HttpResponseRedirect(reverse('reservations:my_reservations'))

#     context = {
#         'formset_data': formset_data,
#         'formset': formset,
#         'reservation_period_id': reservation_period_id,
#         'school_user_id': school_user_id,
#     }

#     return render(request, 'reservations/preview_reservation2.html', context)


def preview_reservation(request, reservation_period_id, school_user_id):

    #date = request.GET.get('date')
    date = request.GET.get('date') or request.POST.get('date')
    res_period = get_object_or_404(ReservationPeriod, pk=reservation_period_id)
    # Retrieve formset data from the session

    #formset_data = request.session.get('formset_data', None)
    formset_data = request.session.get('formset_data', [])

    # print('--------')
    # print(formset_data)

    # Extract the data for each form from formset_data
    form_data_list = [data for data in formset_data if data]
    # print('--------')
    # print(form_data_list)

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
    
    #formset = ReservationFormSet(initial=form_data_list, preview_page=True)
    #formset = ReservationFormSet(request.POST or None, initial=form_data_list, request=request)
    formset = ReservationFormSet(request.POST or None, initial=form_data_list)

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
                                           **form_data)


            # Clear the session data
            request.session.pop('formset_data', None)

            # Redirect to a success page or another view
            return HttpResponseRedirect(reverse('reservations:my_reservations'))

    return render(request, 'reservations/preview_reservation3.html', {'formset': formset,
                                                                        'reservation_period_id': reservation_period_id,
                                                                        'school_user_id': school_user_id,
                                                                        'date': date,
                                                                        })
    

# def preview_reservation(request, reservation_period_id, school_user_id):

#     date = request.GET.get('date') or request.POST.get('date')
#     res_period = get_object_or_404(ReservationPeriod, pk=reservation_period_id)
    
#     # Retrieve formset data from the session
#     formset_data = request.session.get('formset_data', [])
#     print(formset_data)

#     # Instantiate ReservationFormSetClass using formset_factory
#     ReservationFormSetClass = formset_factory(ReservationForm, extra=0, max_num=3, formset=BaseReservationFormSet)
#     formset = ReservationFormSetClass(initial=formset_data)

#     if request.method == 'POST':
#         # Do not pass the 'queryset' parameter here
#         formset = ReservationFormSetClass(request.POST)

#         if formset.is_valid():
#             # Process and save formset data to the model
#             for form_data in formset.cleaned_data:
#                 # timeslot = form_data['timeslot'].id
#                 # Reservation.objects.create(timeslot=timeslot, **form_data)
#                 selected_date_id = Day.objects.get(date=date).id

#                 timeslot_instance = form_data.pop('timeslot')  # Remove 'timeslot' from form_data
#                 print(timeslot_instance)
#                 timeslot_id = timeslot_instance.id
#                 print(timeslot_id)
#                 Reservation.objects.create(timeslot_id=timeslot_id, 
#                                            reservation_period=ReservationPeriod.objects.get(id=reservation_period_id), 
#                                            schoolUser=SchoolUser.objects.get(id=school_user_id),
#                                            reservation_date=Day.objects.get(id=selected_date_id),
#                                            **form_data)

#             # Clear the session data
#             request.session.pop('formset_data', None)

#             # Redirect to a success page or another view
#             return HttpResponseRedirect(reverse('reservations:my_reservations'))


#     return render(request, 'reservations/preview_readonly.html', {'formset': formset,
#                                                                 'reservation_period_id': reservation_period_id,
#                                                                 'school_user_id': school_user_id,
#                                                                 'date': date,
#                                                                   })


@login_required
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

# def modify_timeslots(request, reservation_period_id):
#     reservation_period = get_object_or_404(ReservationPeriod, id=reservation_period_id)
    
#     selected_date = request.GET.get('date')
#     selected_day = get_object_or_404(Day, date=selected_date)

#     # Fetch all timeslots for the selected date
#     timeslots = Timeslot.objects.filter(dayTime__day=selected_day)
#     print(len(timeslots))

#     return render(request, 'reservations/modify_timeslots.html', {
#         'reservation_period': reservation_period,
#         'selected_day': selected_day,
#         'timeslots': timeslots,
#     })

# def exceptional_timeslots(request, reservation_period_id):
#     selected_date = request.GET.get('date')
#     selected_day = get_object_or_404(Day, date=selected_date)

#     # Get the day of the week for the selected date
#     day_of_week_mapping = {
#         0: 'a',  # Monday
#         1: 'b',  # Tuesday
#         2: 'c',  # Wednesday
#         3: 'd',  # Thursday
#         4: 'e',  # Friday
#         5: 'f',  # Saturday
#         6: 'g',  # Sunday
#     }
#     selected_day_of_week = day_of_week_mapping[selected_day.date.weekday()]

#     # Find the corresponding DayTime instances for the determined day
#     available_daytimes = DayTime.objects.filter(day=selected_day_of_week)

#     # Get the UnavailableTime instances for the selected date
#     exceptional_timeslots = ExceptionalRule.objects.filter(date=selected_day)

#     context = {
#         'selected_date': selected_date,
#         'available_daytimes': available_daytimes,
#         'exceptional_timeslots': exceptional_timeslots,
#         'reservation_period_id': reservation_period_id,
#     }

#     return render(request, 'reservations/exceptional_timeslots.html', context)

# def update_exceptional_timeslots(request, reservation_period_id):
#     if request.method == 'POST':
#         selected_date = request.POST.get('selected_date')
#         selected_day = get_object_or_404(Day, date=selected_date)

#         # Get the selected timeslot IDs from the form submission
#         selected_timeslots = request.POST.getlist('timeslots')

#         # Get or create UnavailableTime instances for the selected date and timeslots
#         for timeslot_id in selected_timeslots:
#             timeslot = get_object_or_404(DayTime, id=timeslot_id)
#             exceptional_timeslot_instance, created = ExceptionalRule.objects.get_or_create(date=selected_day, timeslot=timeslot)
#             #exceptional_timeslot_instance.is_reservation_allowed = False  # You can change this based on your form input
#             exceptional_timeslot_instance.save()

#     return redirect('reservations:exceptional_timeslots', reservation_period_id=reservation_period_id)

# def create_exceptional_rule(request):
#     selected_date = request.GET.get('date')

#     # Get the selected day and corresponding DayTime instances
#     selected_day = Day.objects.get(date=selected_date)
#     day_of_week_mapping = {
#         'Monday': 'a',
#         'Tuesday': 'b',
#         'Wednesday': 'c',
#         'Thursday': 'd',
#         'Friday': 'e',
#         'Saturday': 'f',
#         'Sunday': 'g',
#     }
#     selected_day_of_week = day_of_week_mapping[selected_day.date.strftime('%A')]

#     # Find the corresponding DayTime instances for the determined day
#     available_daytimes = DayTime.objects.filter(day=selected_day_of_week)

#     context = {
#         'selected_date': selected_date,
#         'available_daytimes': available_daytimes,
#     }

#     return render(request, 'reservations/create_exceptional_rule.html', context)
