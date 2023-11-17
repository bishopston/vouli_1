from django.db import models
#from django.contrib.auth.models import User
from accounts.models import CustomUser

# Model for defining days
class Day(models.Model):
    date = models.DateField(unique=True)

# Model for defining available timeslots
class DayTime(models.Model):
    DAY_CHOICES = [
        ('a', 'Δευτέρα'),
        ('b', 'Τρίτη'),
        ('c', 'Τετάρτη'),
        ('d', 'Πέμπτη'),
        ('e', 'Παρασκευή'),
        ('f', 'Σάββατο'),
        ('g', 'Κυριακή'),
    ]
    day = models.CharField(max_length=1, choices=DAY_CHOICES)
    slot = models.TimeField()

    def __str__(self):
        return f"{self.get_day_display()} - {self.slot}"

class SchoolYear(models.Model):
    start_date = models.DateField()
    end_date = models.DateField()
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class ReservationPeriod(models.Model):
    schoolYear = models.ForeignKey(SchoolYear, on_delete=models.CASCADE, default=None)
    start_date = models.DateField()
    end_date = models.DateField()
    name = models.CharField(max_length=100)
    is_available = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Timeslot(models.Model):
    dayTime = models.ForeignKey(DayTime, on_delete=models.CASCADE)
    reservation_period = models.ForeignKey(ReservationPeriod, on_delete=models.CASCADE)
    is_reservation_allowed = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.dayTime}, Reservation Allowed: {self.is_reservation_allowed}"

class ExceptionalRule(models.Model):
    date = models.ForeignKey(Day, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    is_reservation_allowed = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.date} {self.timeslot}, Reservation Allowed: {self.is_reservation_allowed}"

class Reservation(models.Model):
    reservation_date = models.ForeignKey(Day, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    reservation_window = models.ForeignKey('ReservationWindow', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.reservation_date} {self.timeslot} - {self.user}"

class ReservationWindow(models.Model):
    reservation_period = models.ForeignKey('ReservationPeriod', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

    def is_reservation_allowed(self, reservation_date):
        return self.start_date <= reservation_date <= self.end_date