from django.contrib import admin
from .models import Day, DayTime, SchoolYear, ReservationPeriod, Timeslot, ExceptionalRule, Reservation, ReservationWindow
from .forms import TimeslotForm, ReservationPeriodForm

class TimeslotInline(admin.TabularInline):
    model = Timeslot
    form = TimeslotForm

class ReservationPeriodInline(admin.TabularInline):
    model = ReservationPeriod
    form = ReservationPeriodForm

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ['date', 'is_vacation']

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
class ExceptionalRuleAdmin(admin.ModelAdmin):
    list_display = ['date', 'timeslot', 'is_reservation_allowed']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['reservation_date', 'timeslot']

@admin.register(ReservationWindow)
class ReservationWindowAdmin(admin.ModelAdmin):
    list_display = ['start_date', 'end_date', 'reservation_period']