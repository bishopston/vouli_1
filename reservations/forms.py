from django import forms
from .models import ReservationPeriod, Timeslot

class TimeslotForm(forms.ModelForm):
    class Meta:
        model = Timeslot
        fields = ['dayTime', 'is_reservation_allowed']

class ReservationPeriodForm(forms.ModelForm):
    class Meta:
        model = ReservationPeriod
        fields = ['name', 'start_date', 'end_date']