from django import forms
from .models import ReservationPeriod, Timeslot

class TimeslotForm(forms.ModelForm):
    class Meta:
        model = Timeslot
        fields = ['dayTime', 'is_reservation_allowed']
