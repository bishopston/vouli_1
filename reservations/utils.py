from datetime import datetime
from .models import Day, Timeslot

def get_occupied_daytimes(selected_date, reservation_period):
    day_of_week_mapping = {
        'Monday': 'a',
        'Tuesday': 'b',
        'Wednesday': 'c',
        'Thursday': 'd',
        'Friday': 'e',
        'Saturday': 'f',
        'Sunday': 'g',
    }

    selected_date_format = datetime.strptime(selected_date, "%Y-%m-%d")

    day_of_week = day_of_week_mapping[selected_date_format.strftime('%A')]

    selected_date_id = Day.objects.get(date=selected_date).id
    
    # Retrieve occupied timeslots for the selected date and reservation period
    occupied_daytimes = Timeslot.objects.filter(
        dayTime__day=day_of_week,
        reservation_period=reservation_period,
        reservation__reservation_date=selected_date_id
    )

    #non_occupied_daytimes = available_daytimes.exclude(id__in=occupied_timeslots)

    return occupied_daytimes

def get_allowed_daytimes(selected_date, reservation_period):
    day_of_week_mapping = {
        'Monday': 'a',
        'Tuesday': 'b',
        'Wednesday': 'c',
        'Thursday': 'd',
        'Friday': 'e',
        'Saturday': 'f',
        'Sunday': 'g',
    }

    selected_date_format = datetime.strptime(selected_date, "%Y-%m-%d")

    day_of_week = day_of_week_mapping[selected_date_format.strftime('%A')]

    # Retrieve allowed timeslots for the selected date and reservation period
    allowed_daytimes = Timeslot.objects.filter(
        dayTime__day=day_of_week,
        reservation_period=reservation_period,
        is_reservation_allowed=True
    )

    return allowed_daytimes
