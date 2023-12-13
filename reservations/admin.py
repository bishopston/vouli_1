from django.contrib import admin
from django import forms
from .models import Day, DayTime, SchoolYear, ReservationPeriod, Timeslot, ExceptionalRule, Reservation, ReservationWindow
from .forms import TimeslotForm, ReservationPeriodForm, ExceptionalRuleAdminForm


class TimeslotInline(admin.TabularInline):
    model = Timeslot
    form = TimeslotForm

class ReservationPeriodInline(admin.TabularInline):
    model = ReservationPeriod
    form = ReservationPeriodForm

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ['date', 'is_vacation']
    list_filter = ['date', 'is_vacation']
    search_fields = ['date']
    date_hierarchy = 'date'
    ordering = ['date']

@admin.register(DayTime)
class DayTimeAdmin(admin.ModelAdmin):
    list_display = ['day', 'slot']

@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date']
    inlines = [ReservationPeriodInline]

@admin.register(ReservationPeriod)
class ReservationPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date', 'is_available']
    inlines = [TimeslotInline]

@admin.register(Timeslot)
class TimeslotAdmin(admin.ModelAdmin):
    list_display = ['dayTime', 'reservation_period', 'is_reservation_allowed']

@admin.register(ExceptionalRule)
class ExceptionalRule(admin.ModelAdmin):
    list_display = ['date', 'timeslot', 'is_reservation_allowed']
    list_filter = ['date']
    ordering = ['date']

# class ExceptionalRuleAdminForm(forms.ModelForm):
#     class Meta:
#         model = ExceptionalRule
#         fields = '__all__'
#         widgets = {
#             'date': forms.DateInput(attrs={'type': 'date'}),
#         }

# class ExceptionalRuleAdmin(admin.ModelAdmin):
#     form = ExceptionalRuleAdminForm

#     def formfield_for_foreignkey(self, db_field, request, **kwargs):
#         if db_field.name == 'timeslot':
#             # Get the date from the request
#             date_str = request.GET.get('date')
            
#             if date_str:
#                 # Convert the date string to a datetime object
#                 date = datetime.strptime(date_str, "%Y-%m-%d").date()
                
#                 # Get the day of the week for the given date
#                 day_of_week = date.strftime('%a').lower()
                
#                 # Filter the available timeslots based on the day of the week
#                 kwargs["queryset"] = Timeslot.objects.filter(dayTime__day=day_of_week)

#         return super().formfield_for_foreignkey(db_field, request, **kwargs)

# admin.site.register(ExceptionalRule, ExceptionalRuleAdmin)

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['reservation_date', 'timeslot']
    list_filter = ['reservation_period__name','reservation_date__date']
    ordering = ['reservation_period__name','reservation_date__date', 'timeslot__dayTime__slot']

@admin.register(ReservationWindow)
class ReservationWindowAdmin(admin.ModelAdmin):
    list_display = ['start_date', 'end_date', 'reservation_period']