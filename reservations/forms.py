from django import forms
from django.forms import BaseFormSet, DateField
from django.core.exceptions import ValidationError
from django.contrib.admin.widgets import AdminDateWidget
from django.db.models import Q
from django.forms.widgets import SelectDateWidget
from django.conf import settings
from .models import ReservationPeriod, Timeslot, Reservation, ExceptionalRule, Day
from .utils import get_occupied_daytimes, get_allowed_daytimes, get_occupied_exceptional_daytimes, get_allowed_exceptional_daytimes
from datetime import datetime

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
            # allowed_daytimes = get_allowed_daytimes(selected_date, reservation_period)
            # occupied_daytimes = get_occupied_daytimes(selected_date, reservation_period)



            #selected_date = datetime.strptime(selected_date, "%Y-%m-%d")
            selected_calendar_date = Day.objects.get(date=selected_date)

            if len(ExceptionalRule.objects.filter(date = selected_calendar_date)) > 0:

                reservations_on_date = Reservation.objects.filter(reservation_date=selected_calendar_date).exclude(status='denied')
                reservation_daytimes = [reservation.timeslot.dayTime for reservation in reservations_on_date]
                non_occupied_daytimes = ExceptionalRule.objects.filter(date=selected_calendar_date,is_reservation_allowed=True).exclude(timeslot__in=reservation_daytimes).order_by('timeslot__slot')
                non_occupied_timeslots = [Timeslot.objects.get(dayTime=rule.timeslot, reservation_period=reservation_period) for rule in non_occupied_daytimes]
                non_occupied_timeslot_ids = [timeslot.id for timeslot in non_occupied_timeslots]
                q_objects = Q()
                for timeslot_id in non_occupied_timeslot_ids:
                    q_objects |= Q(id=timeslot_id)
                non_occupied_timeslots_queryset = Timeslot.objects.filter(q_objects).order_by('dayTime__slot')

                # #*************************************
                # allowed_daytimes = get_allowed_exceptional_daytimes(selected_date, reservation_period)
                # occupied_daytimes = get_occupied_exceptional_daytimes(selected_date, reservation_period)

                # # Look up equivalent Timeslot instances for occupied_daytimes
                # occupied_timeslots = [Timeslot.objects.get(dayTime=rule.timeslot, reservation_period=reservation_period) for rule in occupied_daytimes]


                # # Calculate available_timeslots by excluding occupied timeslots
                # #non_occupied_daytimes = allowed_daytimes.exclude(id__in=occupied_daytimes)
                # non_occupied_daytimes = [daytime for daytime in allowed_daytimes if daytime not in occupied_timeslots]

                # # Convert the list to a queryset
                # non_occupied_daytimes_queryset = Timeslot.objects.filter(id__in=[daytime.id for daytime in non_occupied_daytimes])
                # #*************************************


                # Set choices for the timeslot field based on available_timeslots

            

                self.fields['timeslot'].queryset = non_occupied_timeslots_queryset
                self.fields['timeslot'].label_from_instance = lambda obj: obj.display_time()


            else:

                allowed_daytimes = get_allowed_daytimes(selected_date, reservation_period)
                occupied_daytimes = get_occupied_daytimes(selected_date, reservation_period)

                # Calculate available_timeslots by excluding occupied timeslots
                non_occupied_daytimes = allowed_daytimes.exclude(id__in=occupied_daytimes)

                # Set choices for the timeslot field based on available_timeslots
                self.fields['timeslot'].queryset = non_occupied_daytimes

                # Customize the display of timeslots
                self.fields['timeslot'].label_from_instance = lambda obj: obj.display_time()



            # # Calculate available_timeslots by excluding occupied timeslots
            # non_occupied_daytimes = allowed_daytimes.exclude(id__in=occupied_daytimes)

            # # Set choices for the timeslot field based on available_timeslots
            # self.fields['timeslot'].queryset = non_occupied_daytimes

            # # Customize the display of timeslots
            # self.fields['timeslot'].label_from_instance = lambda obj: obj.display_time()


    # def clean(self):
    #     cleaned_data = super().clean()

    #     # If timeslot is selected, ensure other fields are also provided
    #     if cleaned_data.get('timeslot'):
    #         if not cleaned_data.get('student_number'):
    #             self.add_error('student_number', 'This field is required.')
    #         if not cleaned_data.get('teacher_number'):
    #             self.add_error('teacher_number', 'This field is required.')
    #         if not cleaned_data.get('terms_accepted'):
    #             self.add_error('terms_accepted', 'This field is required.')
    #     return cleaned_data

class BaseReservationFormSet(BaseFormSet):
    def __init__(self, *args, **kwargs):
        reservation_period = kwargs.pop('reservation_period', None)
        selected_date = kwargs.pop('selected_date', None)

        super(BaseReservationFormSet, self).__init__(*args, **kwargs)

        for form in self.forms:
            if reservation_period and selected_date:
                # allowed_daytimes = get_allowed_daytimes(selected_date, reservation_period)
                # occupied_daytimes = get_occupied_daytimes(selected_date, reservation_period)


                #selected_date = datetime.strptime(selected_date, "%Y-%m-%d")
                selected_calendar_date = Day.objects.get(date=selected_date)

                if len(ExceptionalRule.objects.filter(date = selected_calendar_date)) > 0:


                    reservations_on_date = Reservation.objects.filter(reservation_date=selected_calendar_date).exclude(status='denied')
                    reservation_daytimes = [reservation.timeslot.dayTime for reservation in reservations_on_date]
                    non_occupied_daytimes = ExceptionalRule.objects.filter(date=selected_calendar_date,is_reservation_allowed=True).exclude(timeslot__in=reservation_daytimes).order_by('timeslot__slot')
                    non_occupied_timeslots = [Timeslot.objects.get(dayTime=rule.timeslot, reservation_period=reservation_period) for rule in non_occupied_daytimes]
                    non_occupied_timeslot_ids = [timeslot.id for timeslot in non_occupied_timeslots]
                    q_objects = Q()
                    for timeslot_id in non_occupied_timeslot_ids:
                        q_objects |= Q(id=timeslot_id)
                    non_occupied_timeslots_queryset = Timeslot.objects.filter(q_objects).order_by('dayTime__slot')

                    # # #*************************************
                    # allowed_daytimes = get_allowed_exceptional_daytimes(selected_date, reservation_period)
                    # occupied_daytimes = get_occupied_exceptional_daytimes(selected_date, reservation_period)

                    # # Look up equivalent Timeslot instances for occupied_daytimes
                    # occupied_timeslots = [Timeslot.objects.get(dayTime=rule.timeslot, reservation_period=reservation_period) for rule in occupied_daytimes]


                    # # Calculate available_timeslots by excluding occupied timeslots
                    # #non_occupied_daytimes = allowed_daytimes.exclude(id__in=occupied_daytimes)
                    # non_occupied_daytimes = [daytime for daytime in allowed_daytimes if daytime not in occupied_timeslots]

                    # # Convert the list to a queryset
                    # non_occupied_daytimes_queryset = Timeslot.objects.filter(id__in=[daytime.id for daytime in non_occupied_daytimes])
                    # # #*************************************


                    form.fields['timeslot'].queryset = non_occupied_timeslots_queryset
                    form.fields['timeslot'].label_from_instance = lambda obj: obj.display_time()

                else:

                    allowed_daytimes = get_allowed_daytimes(selected_date, reservation_period)
                    occupied_daytimes = get_occupied_daytimes(selected_date, reservation_period)
                    non_occupied_daytimes = allowed_daytimes.exclude(id__in=occupied_daytimes)

                    form.fields['timeslot'].queryset = non_occupied_daytimes
                    form.fields['timeslot'].label_from_instance = lambda obj: obj.display_time()



                # Calculate available_timeslots by excluding occupied timeslots
                # non_occupied_daytimes = allowed_daytimes.exclude(id__in=occupied_daytimes)

            # form.fields['timeslot'].queryset = non_occupied_daytimes
            # form.fields['timeslot'].label_from_instance = lambda obj: obj.display_time()

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

class ReservationUpdateForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ('student_number', 'teacher_number', 'amea')
        labels = {
            'student_number': 'ΑΡΙΘΜΟΣ ΜΑΘΗΤΩΝ/ΤΡΙΩΝ',
            'teacher_number': 'ΑΡΙΘΜΟΣ ΕΚΠΑΙΔΕΥΤΙΚΩΝ',
            'amea': 'ΑΜΕΑ',
        }

class ReservationUpdateAdminForm(forms.ModelForm):
    # reservation_date = DateField(input_formats=settings.DATE_INPUT_FORMATS)
    class Meta:
        model = Reservation
        fields = ('reservation_date', 'timeslot', 'student_number', 'teacher_number', 'amea')
        labels = {
            'reservation_date': 'ΗΜΕΡΟΜΗΝΙΑ',
            'timeslot': 'ΏΡΑ',
            'student_number': 'ΑΡΙΘΜΟΣ ΜΑΘΗΤΩΝ/ΤΡΙΩΝ',
            'teacher_number': 'ΑΡΙΘΜΟΣ ΕΚΠΑΙΔΕΥΤΙΚΩΝ',
            'amea': 'ΑΜΕΑ',
        }
        # widgets = {
        #     'reservation_date': forms.DateInput(attrs={'type': 'date'}),
        #     # 'timeslot': forms.Select(),  
        # }

    reservation_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    timeslot = forms.ModelChoiceField(
        queryset=Timeslot.objects.all(),  # Adjust the queryset as needed
        widget=forms.Select(),  # You can customize the widget if needed
    )
    # reservation_date = forms.DateField(
    #     widget=forms.DateInput(format='%d/%m/%Y', attrs={'class': 'datepicker'}),
    #     input_formats=('%d/%m/%Y', )
    #     )

        # widgets = {
        #     'reservation_date': forms.DateField(widget=forms.widgets.DateInput(attrs={'type': 'date', 'placeholder': 'dd-mm-yyyy (DOB)', 'class': 'form-control'}),
        #     # 'reservation_date': Calendar(format='%d/%m/%Y'),
        #     'timeslot': forms.Select(attrs={'class': 'form-control'}),
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.reservation_date:
            # Preselect the date associated with the reservation
            self.initial['reservation_date'] = instance.reservation_date.date


        # Update the queryset for timeslot based on the selected reservation_date
        reservation_date = self['reservation_date'].value()
        print(reservation_date)


        day_of_week_mapping = {
            'Monday': 'a',
            'Tuesday': 'b',
            'Wednesday': 'c',
            'Thursday': 'd',
            'Friday': 'e',
            'Saturday': 'f',
            'Sunday': 'g',
        }

        # selected_date_format = datetime.strptime(selected_date, "%Y-%m-%d")

        day_of_week = day_of_week_mapping[reservation_date.strftime('%A')]

        # query timeslots of specific res period
        if reservation_date:
            self.fields['timeslot'].queryset = Timeslot.objects.filter(dayTime__day=day_of_week).filter(reservation_period=Reservation.objects.filter(reservation_date__date=reservation_date)[0].reservation_period.id)


        # if instance and instance.timeslot:
        #     # Update the queryset to include only the preselected timeslot
        #     self.fields['timeslot'].queryset = Timeslot.objects.filter(pk=instance.timeslot.pk)

        # self.fields['reservation_date'].widget = forms.widgets.DateInput(
        #     attrs={
        #         'type': 'date', 'placeholder': 'dd-mm-yyyy (DOB)',
        #         'class': 'form-control'
        #         }
        #     )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     instance = getattr(self, 'instance', None)
    #     if instance and instance.reservation_date:
    #         # Set the initial value for reservation_date
    #         self.initial['reservation_date'] = instance.reservation_date.date

    # reservation_date = forms.ModelChoiceField(
    #     queryset=Day.objects.all(),
    #     widget=SelectDateWidget(attrs={'class': 'form-control'}),
    #     empty_label=None  # Remove the empty label from the dropdown
    # )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     instance = getattr(self, 'instance', None)
    #     if instance and instance.reservation_date:
    #         # Preselect the date associated with the reservation
    #         self.initial['reservation_date'] = instance.reservation_date
    
    timeslot.label = 'ΏΡΑ'
    reservation_date.label = 'ΗΜΕΡΟΜΗΝΙΑ'