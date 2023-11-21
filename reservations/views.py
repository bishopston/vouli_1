from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from .models import Day, ReservationPeriod, Timeslot, DayTime, Reservation, ReservationWindow, SchoolTeam, ExceptionalRule, SchoolYear
from .forms import ReservationForm
from datetime import timedelta
#from calendar import monthrange
import datetime
from datetime import datetime as dt

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

# def calendar_month(request, reservation_period_id=None, year=None, month=None):
#     # If reservation_period_id is provided, get the start date of the reservation period
#     if reservation_period_id:
#         reservation_period = ReservationPeriod.objects.get(pk=reservation_period_id)
#         start_date = reservation_period.start_date
#     else:
#         # If no reservation_period_id is provided, use the current date
#         start_date = timezone.now()

#     # If year and month are not provided, use the start date
#     if not year:
#         year = start_date.year
#     if not month:
#         month = start_date.month

#     # Calculate previous and next months
#     prev_month = start_date - timedelta(days=start_date.day)
#     next_month = start_date + timedelta(days=(32 - start_date.day))


#     # Retrieve days for the current month
#     month_days = get_month_days(year, month)

#     context = {
#         'current_month': f'{year}/{month}',
#         'prev_year': prev_month.year,
#         'prev_month': prev_month.month,
#         'next_year': next_month.year,
#         'next_month': next_month.month,
#         'month_days': month_days,
#         'reservation_period_id': reservation_period.id,
#     }

#     return render(request, 'reservations/calendar_month.html', context)

def calendar_month(request, reservation_period_id=None, year=None, month=None):
    # If reservation_period_id is provided, get the start date of the reservation period
    if reservation_period_id:
        reservation_period = ReservationPeriod.objects.get(pk=reservation_period_id)
        if not year and not month:
            start_date = reservation_period.start_date
        else: 
            start_date = datetime.date(year, month, 1)
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
    month_days = get_month_days(year, month)

    context = {
        'current_month': f'{year}/{month}',
        'prev_year': prev_month.year,
        'prev_month': prev_month.month,
        'next_year': next_month.year,
        'next_month': next_month.month,
        'month_days': month_days,
        'reservation_period_id': reservation_period.id,
    }

    return render(request, 'reservations/calendar_month_3.html', context)

def get_month_days(year, month):
    # Implement your logic to retrieve days for the given month and year
    # For simplicity, assuming a Day model with a 'date' field
    days = Day.objects.filter(date__year=year, date__month=month)
    return chunk_days(days)

def chunk_days(days):
    # Helper function to chunk days into weeks for rendering in the template
    weeks = [days[i:i + 7] for i in range(0, len(days), 7)]
    return weeks

# def make_reservation(request, reservation_period_id):
#     if request.method == 'POST':
#         form = ReservationForm(request.POST)
#         if form.is_valid():
#             # Do additional processing if needed
#             form.save()
#             return redirect('base:home')
#     else:
#         form = ReservationForm()

#     return render(request, 'your_template.html', {'form': form})

def make_reservation(request):
    #query user's reservations
    my_reservations = Reservation.objects.all().filter(schoolTeam__schoolUser__creator=request.user)
    #query closest available reservation period whose start date hasn't come yet
    q = ReservationPeriod.objects.filter(is_available=True).filter(start_date__gte=dt.now()).filter(reservationwindow__start_date__gte=dt.now())
    dates = q.values('start_date').order_by('start_date')
    closest_available_res_period = q.filter(start_date=dates[0]['start_date'])
    #get start date of closest res period
    closest_available_res_period[0].reservationwindow_set.first().start_date
    #check that res window is allowed
    closest_available_res_period[0].reservationwindow_set.first().is_reservation_allowed()