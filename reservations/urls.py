from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    # ... your other URL patterns ...
    path('add_timeslots/<int:reservation_period_id>/', views.add_timeslots, name='add_timeslots'),
]