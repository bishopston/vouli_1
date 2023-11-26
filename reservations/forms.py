from django import forms
from .models import ReservationPeriod, Timeslot, Reservation
from .utils import get_occupied_daytimes, get_allowed_daytimes
from datetime import datetime

class TimeslotForm(forms.ModelForm):
    class Meta:
        model = Timeslot
        fields = ['dayTime', 'is_reservation_allowed']

class ReservationPeriodForm(forms.ModelForm):
    class Meta:
        model = ReservationPeriod
        fields = ['name', 'start_date', 'end_date']

# class ReservationForm(forms.ModelForm):
#     class Meta:
#         model = Reservation
#         fields = ('timeslot', 'student_number', 'teacher_number', 'amea', 'terms_accepted')
#         labels = {
#             'timeslot': 'Ώρα Επίσκεψης',
#             'student_number': 'Αριθμός Μαθητών',
#             'teacher_number': 'Αριθμός Εκπαιδευτικών',
#             'amea': 'Συμμετοχή ΑΜΕΑ',
#             'terms_accepted': 'Αποδοχή Όρων'
#         }

#     def __init__(self, *args, **kwargs):
#         reservation_period = kwargs.pop('reservation_period', None)
#         super().__init__(*args, **kwargs)

#         if reservation_period:
#             selected_date = self.initial.get('reservation_date')
#             if selected_date:
#                 # Get the occupied timeslots for the selected date and reservation period
#                 occupied_timeslots = Reservation.objects.filter(
#                     reservation_date=selected_date,
#                     reservation_period=reservation_period,
#                     status='approved'  # Only consider approved reservations as occupied
#                 ).values_list('timeslot__id', flat=True)

#                 # Filter the available timeslots to exclude occupied ones
#                 available_timeslots = Timeslot.objects.filter(
#                     reservation_period=reservation_period,
#                     is_reservation_allowed=True
#                 ).exclude(id__in=occupied_timeslots)

#                 # Update the choices for the timeslot field
#                 self.fields['timeslot'].queryset = available_timeslots
#             else:
#                 # If the selected date is not available, disable the timeslot field
#                 self.fields['timeslot'].queryset = Timeslot.objects.none()

# class ReservationForm(forms.ModelForm):
#     class Meta:
#         model = Reservation
#         fields = ('timeslot', 'student_number', 'teacher_number', 'amea', 'terms_accepted')
#         labels = {
#             'timeslot': 'Ώρα Επίσκεψης',
#             'student_number': 'Αριθμός Μαθητών',
#             'teacher_number': 'Αριθμός Εκπαιδευτικών',
#             'amea': 'Συμμετοχή ΑΜΕΑ',
#             'terms_accepted': 'Αποδοχή Όρων'
#         }

#     def __init__(self, *args, **kwargs):
#         # Pop 'reservation_period' from kwargs, default to None if not present
#         reservation_period = kwargs.pop('reservation_period', None)

#         super(ReservationForm, self).__init__(*args, **kwargs)

#         # Set choices for the timeslot field based on available_timeslots
#         reservation_period = self.initial.get('res_period_id')
#         if reservation_period:
#             selected_date = self.initial.get('date')

#             if selected_date:

#                 allowed_daytimes = get_allowed_daytimes(selected_date, reservation_period)
#                 occupied_daytimes = get_occupied_daytimes(selected_date, reservation_period)

#                 # Calculate available_timeslots by excluding occupied timeslots
#                 non_occupied_daytimes = allowed_daytimes.exclude(id__in=occupied_daytimes)

#                 # Set choices for the timeslot field based on available_timeslots
#                 self.fields['timeslot'].queryset = non_occupied_daytimes


class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ('timeslot', 'student_number', 'teacher_number', 'amea', 'terms_accepted')
        labels = {
            'timeslot': 'Ώρα Επίσκεψης',
            'student_number': 'Αριθμός Μαθητών',
            'teacher_number': 'Αριθμός Εκπαιδευτικών',
            'amea': 'Συμμετοχή ΑΜΕΑ',
            'terms_accepted': 'Αποδοχή Όρων'
        }

    def __init__(self, *args, **kwargs):
        # Pop 'reservation_period' from kwargs, default to None if not present
        reservation_period = kwargs.pop('reservation_period', None)
        selected_date = kwargs.pop('selected_date', None)

        super(ReservationForm, self).__init__(*args, **kwargs)

        if reservation_period and selected_date:
            allowed_daytimes = get_allowed_daytimes(selected_date, reservation_period)
            occupied_daytimes = get_occupied_daytimes(selected_date, reservation_period)

            # Calculate available_timeslots by excluding occupied timeslots
            non_occupied_daytimes = allowed_daytimes.exclude(id__in=occupied_daytimes)

            # Set choices for the timeslot field based on available_timeslots
            self.fields['timeslot'].queryset = non_occupied_daytimes

            # Customize the display of timeslots
            self.fields['timeslot'].label_from_instance = lambda obj: obj.display_time()