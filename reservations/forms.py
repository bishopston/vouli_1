from django import forms
from django.forms import BaseFormSet
from django.core.exceptions import ValidationError
from django.contrib.admin.widgets import AdminDateWidget
from .models import ReservationPeriod, Timeslot, Reservation, ExceptionalRule
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
        self.fields['terms_accepted'].required = True
        self.fields['terms_accepted'].error_messages = {
            'required': 'Πρέπει να αποδεχτείτε τους όρους συμμετοχής.'
        }
        self.fields['student_number'].error_messages = {
            'required': 'Πρέπει να συμπληρώσετε τον αριθμό των μαθητών/τριών.'
        }
        self.fields['teacher_number'].error_messages = {
            'required': 'Πρέπει να συμπληρώσετε τον αριθμό των εκπαιδευτικών.'
        }

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

    # def clean(self):
    #     if any(self.errors):
    #         # Don't bother validating the formset unless each form is valid on its own
    #         return

    #     timeslots = set()
    #     for form in self.forms:
    #         if form.cleaned_data.get('timeslot'):
    #             timeslot = form.cleaned_data['timeslot']
    #             if timeslot in timeslots:
    #                 raise ValidationError('Έχετε καταχωρίσει δύο φορές την ίδια χρονοθυρίδα.')
    #             timeslots.add(timeslot)
    #         if form.cleaned_data.get('terms_accepted') is False:
    #             raise forms.ValidationError("Πρέπει να αποδεχτείτε τους όρους συμμετοχής.")


    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return

        timeslots = set()
        for i, form in enumerate(self.forms):
            if form.cleaned_data.get('timeslot'):
                timeslot = form.cleaned_data['timeslot']
                if timeslot in timeslots:
                    form.add_error('timeslot', ValidationError('Έχετε καταχωρίσει δύο φορές την ίδια χρονοθυρίδα.'))
                    # Remove the duplicated timeslot from the set to avoid global validation error
                    timeslots.remove(timeslot)
                timeslots.add(timeslot)
            if form.cleaned_data.get('terms_accepted') is False:
                form.add_error('terms_accepted', ValidationError("Πρέπει να αποδεχτείτε τους όρους συμμετοχής."))


        # Check if all forms are empty
        if not any(form.cleaned_data for form in self.forms):
            raise ValidationError("Συμπληρώστε τουλάχιστον μία φόρμα για να πραγματοποιήσετε την κράτηση.")
        
class CustomAdminDateWidget(AdminDateWidget):
    def __init__(self, attrs=None, format=None):
        final_attrs = {'class': 'datepicker'}
        if attrs is not None:
            final_attrs.update(attrs)
        super().__init__(attrs=final_attrs, format=format)

class ExceptionalRuleAdminForm(forms.ModelForm):
    date = forms.DateField(widget=CustomAdminDateWidget)

    class Meta:
        model = ExceptionalRule
        fields = '__all__'


class ExceptionalRuleForm(forms.ModelForm):
    class Meta:
        model = ExceptionalRule
        fields = ['date', 'timeslot', 'is_reservation_allowed']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }