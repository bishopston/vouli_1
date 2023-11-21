from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('add_timeslots/<int:reservation_period_id>/', views.add_timeslots, name='add_timeslots'),
    path('edit_timeslots/<int:reservation_period_id>/', views.edit_timeslots, name='edit_timeslots'),
    path('delete_timeslots/', views.delete_timeslots, name='delete_timeslots'),
    #path('make_reservation/<int:reservation_period_id>/', views.make_reservation, name='make_reservation'),
    path('calendar_month/<int:reservation_period_id>/', views.calendar_month, name='calendar_month'),
    path('calendar_month/<int:reservation_period_id>/<int:year>/<int:month>/', views.calendar_month, name='calendar_month_year'),
    #path('make_reservation/<int:reservation_period_id>/', views.make_reservation, name='make_reservation'),
    path('my_reservations/', views.my_reservations, name='my_reservations'),
]