from django.shortcuts import render, redirect, HttpResponseRedirect
from .models import ReservationPeriod, Timeslot, DayTime

def add_timeslots(request, reservation_period_id):
    reservation_period = ReservationPeriod.objects.get(id=reservation_period_id)
    if request.method == 'POST':
        timeslots = request.POST.getlist('timeslots')
        for timeslot in timeslots:
            day, hour = timeslot.split()
            # Create Timeslot objects based on the selected checkboxes
            Timeslot.objects.create(
                reservation_period=reservation_period,
                dayTime=DayTime.objects.get(day=day, slot=hour),
                is_available=True  # Set the initial availability as True
            )
        return HttpResponseRedirect(request.path_info)

    # Pass the days and hours to the template
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00', '20:00']

    return render(request, 'reservations/add_timeslots.html', {'reservation_period': reservation_period, 'days': days, 'hours': hours})
