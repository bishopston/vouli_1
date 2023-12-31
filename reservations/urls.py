from django.urls import path
from . import views

app_name = 'reservations'

urlpatterns = [
    path('<int:reservation_id>/', views.reservation_details, name='reservation_details'),
    path('reservation/<int:reservation_id>/pdf/', views.ReservationPDFView.as_view(), name='reservation_pdf'),
    path('select_timeslots/', views.timeslot_res_period_selection, name='timeslot_res_period_selection'),
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
    # exceptional rules
    path('select_exceptional_rule/', views.exceptional_rule_res_period_selection, name='exceptional_rule_res_period_selection'),
    path('add_exceptional_rule/', views.add_exceptional_rule, name='add_exceptional_rule'),
    path('edit_exceptional_rule/', views.edit_exceptional_rule, name='edit_exceptional_rule'),
    path('delete_exceptional_rule/', views.delete_exceptional_rule, name='delete_exceptional_rule'),
    # update/delete reservation for user
    path('delete_reservation/<int:reservation_id>/<int:school_user_id>/', views.delete_reservation, name='delete_reservation'),
    path('update_reservation/<int:reservation_id>/<int:school_user_id>/', views.update_reservation, name='update_reservation'),
    path('handle_reservations/', views.handle_reservations, name='handle_reservations'),
    path('update_reservation_admin/<int:reservation_id>/', views.update_reservation_admin, name='update_reservation_admin'),
    path('reservation_history/<int:reservation_id>/', views.reservation_history, name='reservation_history'),
    path('reservation_dashboard/', views.reservation_dashboard, name='reservation_dashboard'),
    path('reservations_created_by_admin/', views.reservations_created_by_admin, name='reservations_created_by_admin'),
    # ajax calls for selection dropdowns
    path('get_reservation_periods/', views.get_reservation_periods, name='get_reservation_periods'),
    path('get_departments/', views.get_departments, name='get_departments'),
    path('get_schoolusers/', views.get_schoolusers, name='get_schoolusers'),
    # calendar for reservations
    path('calendar_reservations/<int:reservation_period_id>/', views.calendar_reservations, name='calendar_reservations'),
    path('calendar_reservations/<int:reservation_period_id>/<int:year>/<int:month>/', views.calendar_reservations, name='calendar_reservations_month_year'),
    path('reservation_details_by_date/', views.reservation_details_by_date, name='reservation_details_by_date'),
    path('calendar_reservations_res_period_selection/', views.calendar_reservations_res_period_selection, name='calendar_reservations_res_period_selection'),
    #statistics per reservation period
    path('statistics_per_period/<int:reservation_id>/', views.statistics_per_period, name='statistics_per_period'),
    path('reservationsPerDayResPeriod/<int:reservation_id>/', views.reservationsPerDayResPeriod, name='reservationsPerDayResPeriod'),
    path('studentsPerDayResPeriod/<int:reservation_id>/', views.studentsPerDayResPeriod, name='studentsPerDayResPeriod'),
    path('reservationsPerDeptResPeriod/<int:reservation_id>/', views.reservationsPerDeptResPeriod, name='reservationsPerDeptResPeriod'),
    path('schoolsPerDeptResPeriod/<int:reservation_id>/', views.schoolsPerDeptResPeriod, name='schoolsPerDeptResPeriod'),
    path('reservationsPerStatusResPeriod/<int:reservation_id>/', views.reservationsPerStatusResPeriod, name='reservationsPerStatusResPeriod'),
    path('reservationsPerPerformedResPeriod/<int:reservation_id>/', views.reservationsPerPerformedResPeriod, name='reservationsPerPerformedResPeriod'),
    path('reservationsPerTimeslotResPeriod/<int:reservation_id>/', views.reservationsPerTimeslotResPeriod, name='reservationsPerTimeslotResPeriod'),
    #statistics per school year
    path('statistics_per_year/<int:schoolYear_id>/', views.statistics_per_year, name='statistics_per_year'),
    path('reservationsPerDaySchoolYear/<int:schoolYear_id>/', views.reservationsPerDaySchoolYear, name='reservationsPerDaySchoolYear'),
    path('reservationsPerResPeriodSchoolYear/<int:schoolYear_id>/', views.reservationsPerResPeriodSchoolYear, name='reservationsPerResPeriodSchoolYear'),
    path('reservationsPerDeptSchoolYear/<int:schoolYear_id>/', views.reservationsPerDeptSchoolYear, name='reservationsPerDeptSchoolYear'),
    path('studentsPerResPeriodSchoolYear/<int:schoolYear_id>/', views.studentsPerResPeriodSchoolYear, name='studentsPerResPeriodSchoolYear'),
    #statistics for all years
    path('statistics_all_years/', views.statistics_all_years, name='statistics_all_years'),
    path('reservationsPerSchoolYearTotal/', views.reservationsPerSchoolYearTotal, name='reservationsPerSchoolYearTotal'),
    path('reservationsPerResPeriodTotal/', views.reservationsPerResPeriodTotal, name='reservationsPerResPeriodTotal'),
    path('studentsPerSchoolYearTotal/', views.studentsPerSchoolYearTotal, name='studentsPerSchoolYearTotal'),
    path('studentsPerResPeriodTotal/', views.studentsPerResPeriodTotal, name='studentsPerResPeriodTotal'),
    path('statistics_period_selection/', views.statistics_period_selection, name='statistics_period_selection'),
]