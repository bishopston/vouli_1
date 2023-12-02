from django.shortcuts import render, redirect, HttpResponseRedirect, get_object_or_404
from django.http import Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.forms import formset_factory
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from .models import Day, ReservationPeriod, Timeslot, DayTime, Reservation, ReservationWindow, ExceptionalRule, SchoolYear
from schools.models import SchoolUser
from .forms import ReservationForm, BaseReservationFormSet, ExceptionalRuleForm
from .utils import get_occupied_daytimes, get_allowed_daytimes
from datetime import timedelta
#from calendar import monthrange
import datetime
from datetime import datetime as dt
import pytz
from datetime import datetime, date

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

def add_exceptional_rule(request):

    # If the form was not submitted via POST, handle accordingly
    #selected_date = request.GET.get('date')
    selected_date = request.GET.get('date') or request.POST.get('selected_date')
    print(selected_date)
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
    print(selected_day)
    selected_day_of_week = day_of_week_mapping[selected_day.date.strftime('%A')]
    print(selected_day_of_week)

    # Find the corresponding DayTime instances for the determined day
    available_daytimes = DayTime.objects.filter(day=selected_day_of_week)
    print(available_daytimes)

    if request.method == 'POST':
        #selected_date = request.POST.get('selected_date')
        #selected_date = request.GET.get('selected_date')
        selected_daytimes = request.POST.getlist('daytimes')
        print(selected_date)

        # Check if the submitted daytimes already exist
        for daytime_id in selected_daytimes:
            print(daytime_id)
            submitted_daytimes = ExceptionalRule.objects.filter(date=Day.objects.get(date=selected_date), timeslot=DayTime.objects.get(id=daytime_id))


            if submitted_daytimes.exists():
                available_daytimes = DayTime.objects.filter(day=selected_day_of_week)
                error_message = 'Έχετε προβεί σε διπλοεγγραφή χρονοθυρίδας. Η ενέργεια ακυρώθηκε.'
                return render(request, 'reservations/add_exceptional_rule.html', {'selected_date': selected_date, 'available_daytimes': available_daytimes, 'error_message': error_message})

            # Create ExceptionalRule instances for the selected daytimes
            else:
                ExceptionalRule.objects.create(
                    date=Day.objects.get(date=selected_date),
                    timeslot=DayTime.objects.get(id=daytime_id),
                )

        # Redirect to a success page or any other page
        return render(request, 'reservations/add_exceptional_rule.html', {'selected_date': selected_date, 'selected_day': selected_day, 'available_daytimes': available_daytimes})

    # else:
    #     # If the form was not submitted via POST, handle accordingly
    #     selected_date = request.GET.get('date')
    #     day_of_week_mapping = {
    #         'Monday': 'a',
    #         'Tuesday': 'b',
    #         'Wednesday': 'c',
    #         'Thursday': 'd',
    #         'Friday': 'e',
    #         'Saturday': 'f',
    #         'Sunday': 'g',
    #     }
    #     #selected_day_of_week = day_of_week_mapping[Day.objects.get(date=selected_date).weekday()]
    #     selected_day = Day.objects.get(date=selected_date)
    #     print(selected_day)
    #     selected_day_of_week = day_of_week_mapping[selected_day.date.strftime('%A')]

    #     # Find the corresponding DayTime instances for the determined day
    #     available_daytimes = DayTime.objects.filter(day=selected_day_of_week)

    return render(request, 'reservations/add_exceptional_rule.html', {'selected_date': selected_date, 'selected_day': selected_day, 'available_daytimes': available_daytimes})


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
    # Implement your logic to retrieve days for the given month and year
    # For simplicity, assuming a Day model with a 'date' field
    res_period = ReservationPeriod.objects.get(pk=res_period_id)
    days = Day.objects.filter(date__gte=res_period.start_date, date__lte=res_period.end_date).filter(date__year=year, date__month=month)
    return chunk_days(days)

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

    allowed_timeslots = get_allowed_daytimes(date, reservation_period_id)
    occupied_timeslots = get_occupied_daytimes(date, reservation_period_id)
    non_occupied_timeslots = allowed_timeslots.exclude(id__in=occupied_timeslots)
    non_occupied_timeslots_count = len(non_occupied_timeslots)

    # form = ReservationForm(
    #     reservation_period=res_period,
    #     selected_date=date,
    #     initial={'reservation_date': date, 'reservation_period': res_period.id}
    # )

    #formset = ReservationFormSet(initial=[{'reservation_date': date, 'reservation_period': res_period.id}] * 3)

    # if request.method == 'POST':
    #     form = ReservationForm(request.POST)
    #     if form.is_valid():
    #         my_reservation = Reservation(
    #             schoolUser = schoolUser,
    #             reservation_date = selected_calendar_date,
    #             timeslot = form.cleaned_data["timeslot"],
    #             teacher_number = form.cleaned_data["teacher_number"],
    #             student_number = form.cleaned_data["student_number"],
    #             amea = form.cleaned_data["amea"],
    #             terms_accepted = form.cleaned_data["terms_accepted"],
    #             reservation_period = res_period,
    #         )
    #         my_reservation.save()
    #         return HttpResponseRedirect(reverse('reservations:my_reservations'))
    # else:
    # #     form = ReservationForm(reservation_period=res_period_id, initial={'reservation_date': date})
    #     form = ReservationForm(
    #         reservation_period=res_period,
    #         selected_date=date,
    #         initial={'reservation_date': date, 'reservation_period': res_period.id}
    #     )

    #ReservationFormSet = formset_factory(extra=3, formset=BaseReservationFormSet)
    context = {} 

    ReservationFormSet = formset_factory(ReservationForm, extra=3, max_num=3, formset=BaseReservationFormSet)

    if request.method == 'POST':
        formset = ReservationFormSet(request.POST, reservation_period=res_period, selected_date=date)
        if formset.is_valid():
            for form in formset:
                # process each form in the formset
                if form.cleaned_data.get('timeslot'):
                    my_reservation = Reservation(
                        schoolUser = schoolUser,
                        reservation_date = selected_calendar_date,
                        timeslot = form.cleaned_data["timeslot"],
                        teacher_number = form.cleaned_data["teacher_number"],
                        student_number = form.cleaned_data["student_number"],
                        amea = form.cleaned_data["amea"],
                        terms_accepted = form.cleaned_data["terms_accepted"],
                        reservation_period = res_period,
                    )
                    my_reservation.save()

            return HttpResponseRedirect(reverse('reservations:my_reservations'))
        
        else:
            # Formset is not valid, include it in the context
            context['formset'] = formset
            # Include specific error messages in the context
            context['timeslot_error'] = any(formset.errors) and formset.errors[0].get('timeslot')
            context['terms_accepted_error'] = any(formset.errors) and formset.errors[0].get('terms_accepted')

            #return render(request, 'reservations/reservation.html', context)
    
    else:
        formset = ReservationFormSet(reservation_period=res_period, selected_date=date)
        

    # context = {
    #     'res_period': res_period,
    #     #'res_period_id': res_period.id,
    #     'schoolUser': schoolUser,
    #     'date': date,
    #     'week_day': selected_calendar_date_name,
    #     'selected_calendar_date_day': selected_calendar_date_day,
    #     'selected_calendar_date_month': selected_calendar_date_month,
    #     'selected_calendar_date_year': selected_calendar_date_year,
    #     'allowed_timeslots': allowed_timeslots,
    #     'occupied_timeslots': occupied_timeslots,
    #     'non_occupied_timeslots': non_occupied_timeslots,
    #     'non_occupied_timeslots_count': non_occupied_timeslots_count,
    #     #'form': form,
    #     'formset': formset,
    # }

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
    })

    return render(request, 'reservations/reservation.html', context)

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
