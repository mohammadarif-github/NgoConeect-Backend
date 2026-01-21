# volunteer/views.py
from core.permissions import IsBusinessAdmin
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user.email_service import EmailService
from user.models import User

from .models import TimeLog, VolunteerProfile
from .serializers import (
    TimeLogCreateSerializer, TimeLogSerializer, VolunteerAdminDetailSerializer,
    VolunteerAdminSerializer, VolunteerApplySerializer,
    VolunteerProfileSerializer, VolunteerReviewSerializer,
    VolunteerUpdateSerializer,
)


# --- Volunteer Views ---
class VolunteerApplyView(APIView):
    """Apply as a volunteer."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Apply as volunteer",
        request=VolunteerApplySerializer,
        responses={201: VolunteerProfileSerializer}
    )
    def post(self, request):
        serializer = VolunteerApplySerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            volunteer = serializer.save()
            
            # Notify Admins
            admins = User.objects.filter(role__in=['admin', 'manager'], is_active=True).values_list('email', flat=True)
            for admin_email in admins:
                EmailService.send_volunteer_application_notification(
                    applicant_name=f"{request.user.first_name} {request.user.last_name}",
                    applicant_email=request.user.email,
                    recipient_email=admin_email
                )

            return Response(
                VolunteerProfileSerializer(volunteer).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VolunteerProfileView(APIView):
    """View and update own volunteer profile."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get my volunteer profile",
        responses={200: VolunteerProfileSerializer}
    )
    def get(self, request):
        try:
            profile = VolunteerProfile.objects.get(user=request.user)
            return Response(VolunteerProfileSerializer(profile).data)
        except VolunteerProfile.DoesNotExist:
            return Response(
                {'error': 'You have not applied as a volunteer yet.'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="Update my volunteer profile",
        request=VolunteerUpdateSerializer,
        responses={200: VolunteerProfileSerializer}
    )
    def patch(self, request):
        try:
            profile = VolunteerProfile.objects.get(user=request.user)
        except VolunteerProfile.DoesNotExist:
            return Response(
                {'error': 'You have not applied as a volunteer yet.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = VolunteerUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(VolunteerProfileSerializer(profile).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminVolunteerListView(APIView):
    """Admin: List all volunteer applications."""
    permission_classes = [IsAuthenticated, IsBusinessAdmin]
    
    @extend_schema(
        summary="List all volunteers (Admin)",
        responses={200: VolunteerAdminSerializer(many=True)}
    )
    def get(self, request):
        status_filter = request.query_params.get('status', None)
        
        volunteers = VolunteerProfile.objects.select_related('user')
        
        if status_filter:
            volunteers = volunteers.filter(application_status=status_filter.upper())
        
        serializer = VolunteerAdminSerializer(volunteers, many=True)
        return Response(serializer.data)


class AdminVolunteerDetailView(APIView):
    """Admin: View and review volunteer application."""
    permission_classes = [IsAuthenticated, IsBusinessAdmin]
    
    def get_object(self, user_id):
        try:
            return VolunteerProfile.objects.select_related('user').get(user_id=user_id)
        except VolunteerProfile.DoesNotExist:
            return None
    
    @extend_schema(
        summary="Get volunteer details (Admin)",
        responses={200: VolunteerAdminDetailSerializer}
    )
    def get(self, request, user_id):
        volunteer = self.get_object(user_id)
        if not volunteer:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response(VolunteerAdminDetailSerializer(volunteer).data)
    
    @extend_schema(
        summary="Approve/Reject volunteer (Admin)",
        request=VolunteerReviewSerializer,
        responses={200: VolunteerAdminSerializer}
    )
    def patch(self, request, user_id):
        volunteer = self.get_object(user_id)
        if not volunteer:
            return Response({'error': 'Volunteer not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = VolunteerReviewSerializer(data=request.data)
        if serializer.is_valid():
            new_status = serializer.validated_data['application_status']
            
            # Logic: Update status AND update User Role if Approved
            volunteer.application_status = new_status
            volunteer.save()
            
            if new_status == 'APPROVED':
                # Only update role if they are not already admin/manager (safety check)
                if volunteer.user.role not in ['admin', 'manager']:
                    volunteer.user.role = 'volunteer'
                    volunteer.user.save()
            
            # Notify Volunteer
            EmailService.send_volunteer_status_update(
                applicant_email=volunteer.user.email,
                applicant_name=f"{volunteer.user.first_name} {volunteer.user.last_name}",
                new_status=new_status
            )
            
            return Response(VolunteerAdminSerializer(volunteer).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# --- Time Log Views ---
class TimeLogListView(APIView):
    """Volunteer: View and create time logs."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get my time logs",
        responses={200: TimeLogSerializer(many=True)}
    )
    def get(self, request):
        logs = TimeLog.objects.filter(volunteer=request.user).select_related('task')
        serializer = TimeLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Log working hours",
        request=TimeLogCreateSerializer,
        responses={201: TimeLogSerializer}
    )
    def post(self, request):
        serializer = TimeLogCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            log = serializer.save()
            return Response(TimeLogSerializer(log).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
