from datetime import datetime
from .models import Day, Timeslot, ExceptionalRule, Reservation

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
    
    # Retrieve occupied timeslots for the selected date and reservation period - exclude the denied
    occupied_daytimes = Timeslot.objects.filter(
        dayTime__day=day_of_week,
        reservation_period=reservation_period,
        reservation__reservation_date=selected_date_id,
    ).exclude(reservation__status='denied')

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
    ).order_by('dayTime__slot')

    return allowed_daytimes

def get_occupied_exceptional_daytimes(selected_date, reservation_period):
    # day_of_week_mapping = {
    #     'Monday': 'a',
    #     'Tuesday': 'b',
    #     'Wednesday': 'c',
    #     'Thursday': 'd',
    #     'Friday': 'e',
    #     'Saturday': 'f',
    #     'Sunday': 'g',
    # }

    # selected_date_format = datetime.strptime(selected_date, "%Y-%m-%d")

    # day_of_week = day_of_week_mapping[selected_date_format.strftime('%A')]

    selected_date_id = Day.objects.get(date=selected_date).id

    # Get reservations made for the specified date - exclude the denied
    reservations_on_date = Reservation.objects.filter(
        reservation_date__date=selected_date
    ).exclude(status='denied')

    # Extract DayTime instances from reservations
    reservation_daytimes = [reservation.timeslot.dayTime for reservation in reservations_on_date]

    # if len(ExceptionalRule.objects.filter(date = selected_date_id)) > 0:

    # Get ExceptionalRule instances for the specified date and DayTime instances with reservations
    occupied_daytimes = ExceptionalRule.objects.filter(
        date=selected_date_id,
        timeslot__in=reservation_daytimes
    ).order_by('timeslot')

    # else:
    #     # Retrieve occupied timeslots for the selected date and reservation period
    #     occupied_daytimes = Timeslot.objects.filter(
    #         dayTime__day=day_of_week,
    #         reservation_period=reservation_period,
    #         reservation__reservation_date=selected_date_id
    #     )

    #non_occupied_daytimes = available_daytimes.exclude(id__in=occupied_timeslots)

    return occupied_daytimes


def get_allowed_exceptional_daytimes(selected_date, reservation_period):
    # day_of_week_mapping = {
    #     'Monday': 'a',
    #     'Tuesday': 'b',
    #     'Wednesday': 'c',
    #     'Thursday': 'd',
    #     'Friday': 'e',
    #     'Saturday': 'f',
    #     'Sunday': 'g',
    # }

    # selected_date_format = datetime.strptime(selected_date, "%Y-%m-%d")

    # day_of_week = day_of_week_mapping[selected_date_format.strftime('%A')]

    selected_date_id = Day.objects.get(date=selected_date).id

    # if len(ExceptionalRule.objects.filter(date = selected_date_id)) > 0:
    allowed_daytimes = ExceptionalRule.objects.filter(
        date = selected_date_id,
        is_reservation_allowed=True
    ).order_by('timeslot__slot')
    # else:
    #     allowed_daytimes = Timeslot.objects.filter(
    #         dayTime__day=day_of_week,
    #         reservation_period=reservation_period,
    #         is_reservation_allowed=True
    #     )

    return allowed_daytimes


# def calculate_availability_percentage(selected_date, reservation_period):

#     selected_date = datetime.strptime(selected_date, "%Y-%m-%d")
#     selected_calendar_date = Day.objects.get(date=selected_date)

#     if len(ExceptionalRule.objects.filter(date = selected_calendar_date)) > 0:

#         allowed_timeslots = get_allowed_exceptional_daytimes(selected_date, reservation_period)
#         occupied_timeslots = get_occupied_exceptional_daytimes(selected_date, reservation_period)

#     else:

#         allowed_timeslots = get_allowed_daytimes(selected_date, reservation_period)
#         occupied_timeslots = get_occupied_daytimes(selected_date, reservation_period)

#     non_occupied_timeslots = allowed_timeslots.exclude(id__in=occupied_timeslots)

#     if non_occupied_timeslots == allowed_timeslots:
#         return 0
#     else:
#         return (non_occupied_timeslots/allowed_timeslots)

def calculate_availability_percentage(selected_date, reservation_period):

    selected_str_date = datetime.strftime(selected_date, "%Y-%m-%d")
    selected_calendar_date = Day.objects.get(date=selected_date)

    if len(ExceptionalRule.objects.filter(date = selected_calendar_date)) > 0:

        allowed_timeslots = get_allowed_exceptional_daytimes(selected_str_date, reservation_period)
        occupied_timeslots = get_occupied_exceptional_daytimes(selected_str_date, reservation_period)

    else:

        allowed_timeslots = get_allowed_daytimes(selected_str_date, reservation_period)
        occupied_timeslots = get_occupied_daytimes(selected_str_date, reservation_period)

    non_occupied_timeslots = allowed_timeslots.exclude(id__in=occupied_timeslots)

    if len(allowed_timeslots) > 0:
        if len(occupied_timeslots) == len(allowed_timeslots):
            return 0
        else:
            return (len(non_occupied_timeslots)/len(allowed_timeslots))
    else:
        return 1

