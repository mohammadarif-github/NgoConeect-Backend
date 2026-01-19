from django.db.models import Sum
from django.utils import timezone
from donations.models import Donation
from drf_spectacular.utils import OpenApiResponse, extend_schema
from projects.models import Campaign, Event, EventParticipant, Task
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user.models import User
from volunteers.models import TimeLog, VolunteerProfile


class DashboardSummaryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Dashboard Summary",
        description="Get dynamic dashboard summary based on user role (Admin/Volunteer/Donor).",
        responses={200: OpenApiResponse(description="Summary data JSON")}
    )
    def get(self, request):
        role = request.user.role
        data = {
            "role": role,
            "user_name": f"{request.user.first_name} {request.user.last_name}".strip() or request.user.email
        }

        if role in ['admin', 'manager']:
            total_donations = Donation.objects.filter(status='SUCCESS').aggregate(t=Sum('amount'))['t'] or 0
            data.update({
                "total_users": User.objects.count(),
                "total_donations": total_donations,
                "active_campaigns": Campaign.objects.filter(status='ACTIVE').count(),
                "pending_volunteers": VolunteerProfile.objects.filter(application_status='PENDING').count()
            })
        
        elif role == 'volunteer':
            try:
                profile = VolunteerProfile.objects.get(user=request.user)
                status = profile.application_status
            except VolunteerProfile.DoesNotExist:
                status = "NOT_APPLIED"

            hours = TimeLog.objects.filter(volunteer=request.user).aggregate(t=Sum('duration_minutes'))['t'] or 0
            
            # Upcoming events
            upcoming = EventParticipant.objects.filter(
                volunteer=request.user, 
                event__start_datetime__gte=timezone.now()
            ).count()

            data.update({
                "application_status": status,
                "hours_logged_minutes": hours,
                "assigned_tasks_pending": Task.objects.filter(assigned_to=request.user, is_completed=False).count(),
                "upcoming_events_count": upcoming
            })

        else: # Donor, General User
            my_donations = Donation.objects.filter(donor=request.user, status='SUCCESS').aggregate(t=Sum('amount'))['t'] or 0
            data.update({
                "my_total_donations": my_donations,
                "active_campaigns_count": Campaign.objects.filter(status='ACTIVE').count()
            })

        return Response(data)
