from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('add_timeslots/<int:reservation_period_id>/', views.add_timeslots, name='add_timeslots'),
    path('edit_timeslots/<int:reservation_period_id>/', views.edit_timeslots, name='edit_timeslots'),
    path('delete_timeslots/', views.delete_timeslots, name='delete_timeslots'),
    path('calendar_month/<int:reservation_period_id>/<int:school_user_id>/', views.calendar_month, name='calendar_month'),
    path('calendar_month/<int:reservation_period_id>/<int:school_user_id>/<int:year>/<int:month>/', views.calendar_month, name='calendar_month_year'),
    path('make_reservation/<int:reservation_period_id>/<int:school_user_id>/', views.make_reservation, name='make_reservation'),
    path('preview_reservation/<int:reservation_period_id>/<int:school_user_id>/', views.preview_reservation, name='preview_reservation'),
    path('my_reservations/', views.my_reservations, name='my_reservations'),
    path('calendar_timeslot/<int:reservation_period_id>/', views.calendar_timeslot, name='calendar_timeslot'),
    path('calendar_timeslot/<int:reservation_period_id>/<int:year>/<int:month>/', views.calendar_timeslot, name='calendar_timeslot_month_year'),
    path('add_exceptional_rule/', views.add_exceptional_rule, name='add_exceptional_rule'),
    path('edit_exceptional_rule/', views.edit_exceptional_rule, name='edit_exceptional_rule'),
    path('delete_exceptional_rule/', views.delete_exceptional_rule, name='delete_exceptional_rule'),
    path('delete_reservation/<int:reservation_id>/<int:school_user_id>/', views.delete_reservation, name='delete_reservation'),
    path('update_reservation/<int:reservation_id>/<int:school_user_id>/', views.update_reservation, name='update_reservation'),
]