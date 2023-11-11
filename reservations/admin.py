from django.contrib import admin
from .models import Day, DayTime, ReservationPeriod, Timeslot, ExceptionalRule, Reservation
from .forms import TimeslotForm

class TimeslotInline(admin.TabularInline):
    model = Timeslot
    form = TimeslotForm

@admin.register(Day)
class DayAdmin(admin.ModelAdmin):
    list_display = ['date']

@admin.register(DayTime)
class DayTimeAdmin(admin.ModelAdmin):
    list_display = ['day', 'slot']

@admin.register(ReservationPeriod)
class ReservationPeriodAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_date', 'end_date']
    inlines = [TimeslotInline]

@admin.register(Timeslot)
class TimeslotAdmin(admin.ModelAdmin):
    list_display = ['dayTime', 'reservation_period', 'is_available', 'is_reservation_allowed']

@admin.register(ExceptionalRule)
class ExceptionalRuleAdmin(admin.ModelAdmin):
    list_display = ['date', 'timeslot', 'is_available', 'is_reservation_allowed']

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ['reservation_date', 'timeslot', 'user', 'reservation_window']

