from django.shortcuts import render, redirect, HttpResponseRedirect
from django.http import Http404
from django.urls import reverse
from .models import ReservationPeriod, Timeslot, DayTime

# def add_timeslots(request, reservation_period_id):
#     #reservation_period = ReservationPeriod.objects.get(id=reservation_period_id)
#     try:
#         reservation_period = ReservationPeriod.objects.get(pk=reservation_period_id)
#     except ReservationPeriod.DoesNotExist:
#         raise Http404("Reservation period does not exist")
    
#     if request.method == 'POST':
#         timeslots = request.POST.getlist('timeslots')

#         # Check for duplicate timeslots before saving
#         for selected_timeslot in timeslots:
            
#             day, time = selected_timeslot.split('_')
#             existing_timeslots = Timeslot.objects.filter(reservation_period=reservation_period, dayTime__day=day, dayTime__slot=time)


#         if existing_timeslots.exists():
#             return render(request.path_info, {'error_message': "Έχετε προβεί σε διπλοεγγραφή χρονοθυρίδας"})
        
#         else:
#             for timeslot in timeslots:
#                 day, hour = timeslot.split('_')
#                 # Create Timeslot objects based on the selected checkboxes
#                 print(f"Day: {day}, Hour: {hour}")
#                 day_str = DayTime.DAY_CHOICES[int(day)][1]
#                 #day_str = day.capitalize()
#                 Timeslot.objects.create(
#                     reservation_period=reservation_period,
#                     dayTime = DayTime.objects.get(day=day_str, slot=hour),
#                     is_reservation_allowed=True
#                 )
#         return HttpResponseRedirect(request.path_info)

#     # Pass the days and hours to the template
#     days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
#     hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00']

#     return render(request, 'reservations/add_timeslots.html', {'reservation_period': reservation_period, 'days': days, 'hours': hours})


def add_timeslots(request, reservation_period_id):

    # Pass the days and hours to the template
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00']

    reservation_period = ReservationPeriod.objects.get(id=reservation_period_id)
    if request.method == 'POST':
        timeslots = request.POST.getlist('timeslots')

        for timeslot in timeslots:
            day, hour = timeslot.split()
            submitted_timeslots = Timeslot.objects.filter(reservation_period=reservation_period, dayTime__day=day, dayTime__slot=hour)

            if submitted_timeslots.exists():
                return render(request, 'reservations/add_timeslots.html', {'reservation_period': reservation_period, 'days': days, 'hours': hours, 'error_message': 'Έχετε προβεί σε διπλοεγγραφή χρονοθυρίδας'})

            else:
                # Create Timeslot objects based on the selected checkboxes
                Timeslot.objects.create(
                    reservation_period=reservation_period,
                    dayTime=DayTime.objects.get(day=day, slot=hour),
                    is_available=True  # Set the initial availability as True
                )
        return HttpResponseRedirect(request.path_info)

    return render(request, 'reservations/add_timeslots.html', {'reservation_period': reservation_period, 'days': days, 'hours': hours})


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


def delete_timeslots(request):
    if request.method == "POST":
        timeslot_ids = request.POST.getlist('id[]')
        for id in timeslot_ids:
            tslot = Timeslot.objects.get(pk=id)
            tslot.delete()
        return redirect(reverse('schools:schooluser_list'))