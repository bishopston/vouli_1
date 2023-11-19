from django.db import models
#from django.contrib.auth.models import User
#from accounts.models import CustomUser
from schools.models import SchoolUser

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

class SchoolTeam(models.Model):
    TEACHER_NUM = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ]
    STUDENT_NUM = [
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
    schoolUser = models.ForeignKey(SchoolUser, on_delete=models.CASCADE)
    teacher_number = models.CharField(max_length=1, choices=TEACHER_NUM)
    student_number = models.CharField(max_length=2, choices=STUDENT_NUM)
    reservation_period = models.ForeignKey(ReservationPeriod, on_delete=models.CASCADE)
    amea = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.schoolUser.school.name} - {self.reservation_period.name} - {self.id}"

class ReservationWindow(models.Model):
    reservation_period = models.ForeignKey('ReservationPeriod', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.reservation_period}"

    def is_reservation_allowed(self, reservation_date):
        return self.start_date <= reservation_date <= self.end_date


class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Εκκρεμής'),
        ('denied', 'Ακυρωμένη'),
        ('approved', 'Επιβεβαιωμένη'),
    ]
    reservation_date = models.ForeignKey(Day, on_delete=models.CASCADE)
    timeslot = models.ForeignKey(Timeslot, on_delete=models.CASCADE)
    schoolTeam = models.ForeignKey(SchoolTeam, on_delete=models.CASCADE, default=None)
    reservation_window = models.ForeignKey(ReservationWindow, on_delete=models.CASCADE, default=None)
    reservation_period = models.ForeignKey(ReservationPeriod, on_delete=models.CASCADE, default=None)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES)
    is_performed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.reservation_date} {self.timeslot} - {self.user}"

    class Meta:
        # Add a unique constraint to ensure that only one reservation can be made for a specific timeslot on a specific date
        unique_together = ('reservation_date', 'timeslot')


