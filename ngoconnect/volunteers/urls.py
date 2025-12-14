# volunteer/urls.py
from django.urls import path

from .views import (
    AdminVolunteerDetailView, AdminVolunteerListView, TimeLogListView,
    VolunteerApplyView, VolunteerProfileView,
)

urlpatterns = [
    # Volunteer endpoints
    path('apply/', VolunteerApplyView.as_view(), name='volunteer_apply'),
    path('profile/', VolunteerProfileView.as_view(), name='volunteer_profile'),
    path('time-logs/', TimeLogListView.as_view(), name='volunteer_time_logs'),
    
    # Admin endpoints
    path('admin/list/', AdminVolunteerListView.as_view(), name='admin_volunteer_list'),
    path('admin/<int:user_id>/', AdminVolunteerDetailView.as_view(), name='admin_volunteer_detail'),
]