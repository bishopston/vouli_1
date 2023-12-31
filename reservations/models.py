from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from schools.models import SchoolUser
from datetime import datetime as dt
import pytz
from simple_history.models import HistoricalRecords

# Get current UTC time
utc_now = dt.now(pytz.utc)

# Define the Athens time zone
athens_tz = pytz.timezone('Europe/Athens')

# Convert UTC time to Athens time
athens_now = utc_now.astimezone(athens_tz)

# Model for defining days
class Day(models.Model):
    date = models.DateField(unique=True)
    is_vacation = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.date}"

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

    def is_current_year(self):
        return self.start_date <= dt.now(pytz.utc) <= self.end_date

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
        return self.dayTime.slot.strftime('%H:%M')
    
    def display_time(self):
        return self.dayTime.slot.strftime('%H:%M')

class ExceptionalRule(models.Model):
    date = models.ForeignKey(Day, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(DayTime, on_delete=models.CASCADE)
    is_reservation_allowed = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.date} {self.timeslot}, Reservation Allowed: {self.is_reservation_allowed}"
    
    def display_time(self):
        return self.timeslot.slot.strftime('%H:%M')


class ReservationWindow(models.Model):
    reservation_period = models.ForeignKey('ReservationPeriod', on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return f"{self.reservation_period}"

    def is_reservation_allowed(self):
        return self.start_date <= dt.now(pytz.utc) <= self.end_date


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Εκκρεμής'),
        ('denied', 'Ακυρωμένη'),
        ('approved', 'Επιβεβαιωμένη'),
    ]
    TEACHER_NUM = [
        ('', 'Επιλέξτε'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ]
    STUDENT_NUM = [
        ('', 'Επιλέξτε'),
        ('15', '15'),
        ('16', '16'),
        ('17', '17'),
        ('18', '18'),
        ('19', '19'),
        ('20', '20'),
        ('21', '21'),
        ('22', '22'),
        ('23', '23'),
        ('24', '24'),
        ('25', '25'),
        ('26', '26'),
        ('27', '27'),
        ('28', '28'),
        ('29', '29'),
        ('30', '30'),
        ('31', '31'),
        ('32', '32'),
        ('33', '33'),
        ('34', '34'),
        ('35', '35'),
        ('36', '36'),
        ('37', '37'),
        ('38', '38'),
        ('39', '39'),
        ('40', '40'),
        ('41', '41'),
        ('42', '42'),
        ('43', '43'),
        ('44', '44'),
        ('45', '45'),
        ('46', '46'),
        ('47', '47'),
        ('48', '48'),
        ('49', '49'),
        ('50', '50'),
    ]
    schoolUser = models.ForeignKey(SchoolUser, on_delete=models.CASCADE, default=None)
    reservation_date = models.ForeignKey(Day, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    teacher_number = models.CharField(max_length=1, choices=TEACHER_NUM, default='')
    student_number = models.CharField(max_length=2, choices=STUDENT_NUM, default='')
    amea = models.BooleanField(default=False)
    terms_accepted = models.BooleanField(default=False)
    reservation_period = models.ForeignKey(ReservationPeriod, on_delete=models.CASCADE, default=None)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='pending')
    is_performed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    history = HistoricalRecords()

    # @property
    # def _history_user(self):
    #     return self.updated_by

    # @_history_user.setter
    # def _history_user(self, value):
    #     self.updated_by = value

    def __str__(self):
        return f"{self.reservation_date} {self.timeslot}"

    def save(self, *args, **kwargs):

        # Set the user who is updating the reservation
        user = kwargs.pop('user', None)
        if user:
            self.updated_by = user

        # Check if reservation_date is not set (it might be None)
        if self.reservation_date_id is None:
            # If reservation_date is None, raise a ValidationError
            raise ValidationError("Reservation date must be set.")

        # Check if there is an existing reservation with the same date and timeslot
        existing_reservations = Reservation.objects.filter(
            reservation_date=self.reservation_date,
            timeslot=self.timeslot,
        ).exclude(id=self.id)  # Exclude the current instance if it's being updated

        # Check if there are any existing reservations with status 'denied'
        denied_reservations = existing_reservations.filter(status='denied')

        if denied_reservations.exists():
            # If there are denied reservations, allow submitting a new reservation regardless of its status
            super().save(*args, **kwargs)
            return

        self.updated_at = timezone.now()

        # Continue with the save process
        super().save(*args, **kwargs)

    # class Meta:
    #     # Add a unique constraint to ensure that only one reservation can be made for a specific timeslot on a specific date
    #     unique_together = ('reservation_date', 'timeslot')

