from django import forms
from django.forms import BaseFormSet
from django.core.exceptions import ValidationError
from .models import ReservationPeriod, Timeslot, Reservation
from .utils import get_occupied_daytimes, get_allowed_daytimes

class TimeslotForm(forms.ModelForm):
    class Meta:
        model = Timeslot
        fields = ['dayTime', 'is_reservation_allowed']

class ReservationPeriodForm(forms.ModelForm):
    class Meta:
        model = ReservationPeriod
        fields = ['name', 'start_date', 'end_date']

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


class BaseReservationFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        reservation_period = kwargs.pop('reservation_period', None)
        selected_date = kwargs.pop('selected_date', None)

        super(BaseReservationFormSet, self).__init__(*args, **kwargs)

        for form in self.forms:
            if reservation_period and selected_date:
                allowed_daytimes = get_allowed_daytimes(selected_date, reservation_period)
                occupied_daytimes = get_occupied_daytimes(selected_date, reservation_period)

                # Calculate available_timeslots by excluding occupied timeslots
                non_occupied_daytimes = allowed_daytimes.exclude(id__in=occupied_daytimes)

            form.fields['timeslot'].queryset = non_occupied_daytimes
            form.fields['timeslot'].label_from_instance = lambda obj: obj.display_time()

    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        timeslots = set()
        for form in self.forms:
            if form.cleaned_data.get('timeslot'):
                timeslot = form.cleaned_data['timeslot']
                if timeslot in timeslots:
                    raise ValidationError('Έχετε καταχωρίσει δύο φορές την ίδια χρονοθυρίδα')
                timeslots.add(timeslot)
