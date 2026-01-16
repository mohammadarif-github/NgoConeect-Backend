from core.permissions import IsAdminOrReadOnly, IsVolunteerOrAdmin
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import (
    OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema,
)
from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Campaign, Event, EventParticipant, Task
from .serializers import (
    CampaignSerializer, EventParticipantSerializer, EventSerializer,
    TaskSerializer,
)

# -------------------------------------------------------------------
# CAMPAIGN MANAGEMENT (Class-Based Views)
# -------------------------------------------------------------------

class CampaignListCreateView(APIView):
    """
    get: List all campaigns (Public).
    post: Create a new campaign (Admin/Manager only).
    """
    permission_classes = [IsAdminOrReadOnly]

    @extend_schema(
        summary="List Campaigns",
        description="Get a list of all campaigns. Publicly accessible.",
        parameters=[
            OpenApiParameter(name='status', description='Filter by status (e.g., ACTIVE, PLANNED)', required=False, type=str),
        ],
        responses={200: CampaignSerializer(many=True)}
    )
    def get(self, request):
        queryset = Campaign.objects.all().order_by('-start_date')
        
        # Optional: Simple filter by status
        status_param = request.query_params.get('status')
        if status_param:
            queryset = queryset.filter(status=status_param.upper())
            
        serializer = CampaignSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create Campaign",
        description="Create a new campaign. Requires Admin or Manager role.",
        request=CampaignSerializer,
        responses={
            201: CampaignSerializer,
            403: OpenApiResponse(description="Permission Denied")
        }
    )
    def post(self, request):
        serializer = CampaignSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CampaignDetailView(APIView):
    """
    get: Retrieve a specific campaign by Slug.
    put/patch: Update a campaign (Admin/Manager).
    delete: Delete a campaign (Admin/Manager).
    """
    permission_classes = [IsAdminOrReadOnly]

    def get_object(self, slug):
        return get_object_or_404(Campaign, slug=slug)

    @extend_schema(
        summary="Get Campaign Details",
        description="Retrieve details of a campaign by Slug.",
        responses={200: CampaignSerializer, 404: OpenApiResponse(description="Not Found")}
    )
    def get(self, request, slug):
        campaign = self.get_object(slug)
        serializer = CampaignSerializer(campaign)
        return Response(serializer.data)

    @extend_schema(
        summary="Update Campaign",
        description="Update an existing campaign. Admin only.",
        request=CampaignSerializer,
        responses={200: CampaignSerializer}
    )
    def put(self, request, slug):
        campaign = self.get_object(slug)
        serializer = CampaignSerializer(campaign, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        summary="Delete Campaign",
        description="Delete a campaign. Admin only.",
        responses={204: OpenApiResponse(description="Deleted successfully")}
    )
    def delete(self, request, slug):
        campaign = self.get_object(slug)
        campaign.delete()
        return Response({"message": "Campaign deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


# -------------------------------------------------------------------
# TASK MANAGEMENT (Class-Based Views)
# -------------------------------------------------------------------

class TaskListCreateView(APIView):
    """
    get: List tasks (Filterable).
    post: Create a new task (Admin only).
    """
    permission_classes = [IsVolunteerOrAdmin]

    @extend_schema(
        summary="List Tasks",
        description="List all tasks. Volunteers can filter to see only their assigned tasks.",
        parameters=[
            OpenApiParameter(name='campaign_id', description='Filter by Campaign ID', required=False, type=int),
            OpenApiParameter(name='mine', description='Set "true" to see only my tasks', required=False, type=str),
        ],
        responses={200: TaskSerializer(many=True)}
    )
    def get(self, request):
        queryset = Task.objects.all().order_by('due_date')

        # Filter by Campaign ID
        campaign_id = request.query_params.get('campaign_id')
        if campaign_id:
            queryset = queryset.filter(campaign_id=campaign_id)

        # Filter "My Tasks"
        if request.query_params.get('mine') == 'true' and request.user.is_authenticated:
            queryset = queryset.filter(assigned_to=request.user)
            
        serializer = TaskSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Create Task",
        description="Create a new task for a campaign. Admin/Manager only.",
        request=TaskSerializer,
        responses={201: TaskSerializer}
    )
    def post(self, request):
        # Strict Admin Check
        if request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins can create tasks.")

        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskDetailView(APIView):
    """
    get: View task details.
    put/delete: Admin only.
    """
    permission_classes = [IsVolunteerOrAdmin]

    def get_object(self, pk):
        return get_object_or_404(Task, pk=pk)

    @extend_schema(summary="Get Task Details", responses={200: TaskSerializer})
    def get(self, request, pk):
        task = self.get_object(pk)
        serializer = TaskSerializer(task)
        return Response(serializer.data)

    @extend_schema(summary="Update Task (Admin)", request=TaskSerializer)
    def put(self, request, pk):
        if request.user.role not in ['admin', 'manager']:
             raise PermissionDenied("Only admins can update tasks.")
             
        task = self.get_object(pk)
        serializer = TaskSerializer(task, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(summary="Delete Task (Admin)")
    def delete(self, request, pk):
        if request.user.role not in ['admin', 'manager']:
             raise PermissionDenied("Only admins can delete tasks.")
             
        task = self.get_object(pk)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MarkTaskCompleteView(APIView):
    """
    patch: Mark a specific task as completed (Volunteer).
    """
    permission_classes = [IsVolunteerOrAdmin]

    @extend_schema(
        summary="Mark Task as Completed",
        description="Allows a volunteer to mark their assigned task as done.",
        request=None,
        responses={
            200: OpenApiResponse(
                description="Success",
                examples=[
                    OpenApiExample("Success", value={"status": "Task marked as completed"})
                ]
            ),
            403: OpenApiResponse(description="Not your task")
        }
    )
    def patch(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        
        # Check ownership
        if task.assigned_to != request.user and request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("You can only complete tasks assigned to you.")
        
        task.is_completed = True
        task.save()
        
        return Response({"status": "Task marked as completed"}, status=status.HTTP_200_OK)

# -------------------------------------------------------------------
# EVENT MANAGEMENT (Volunteers)
# -------------------------------------------------------------------

class EventListCreateView(APIView):
    """
    get: List all upcoming events.
    post: Create a new event (Admin/Manager only).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List Events",
        description="List all events.",
        responses={200: EventSerializer(many=True)}
    )
    def get(self, request):
        events = Event.objects.all().order_by('start_datetime')
        serializer = EventSerializer(events, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create Event",
        description="Create a new event linked to a campaign. (Admin/Manager only)",
        request=EventSerializer,
        responses={201: EventSerializer}
    )
    def post(self, request):
        if request.user.role not in ['admin', 'manager']:
            raise PermissionDenied("Only admins/managers can create events.")
        
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EventSignupView(APIView):
    """
    post: Volunteer signs up for an event.
    delete: Volunteer cancels signup.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Sign up for Event",
        description="Volunteer registers for an event.",
        request=None,
        responses={
            201: OpenApiResponse(description="Successfully Registered"),
            400: OpenApiResponse(description="Event full or already registered")
        }
    )
    def post(self, request, pk):
        if request.user.role != 'volunteer':
            raise PermissionDenied("Only volunteers can sign up for events.")
            
        event = get_object_or_404(Event, pk=pk)
        
        if event.is_full:
            return Response({"error": "Event is full."}, status=status.HTTP_400_BAD_REQUEST)
            
        if EventParticipant.objects.filter(event=event, volunteer=request.user).exists():
            return Response({"error": "Already registered."}, status=status.HTTP_400_BAD_REQUEST)
            
        signup = EventParticipant.objects.create(event=event, volunteer=request.user, status='REGISTERED')
        return Response({"status": "Successfully registered", "signup_id": signup.id}, status=status.HTTP_201_CREATED)

    @extend_schema(
        summary="Cancel Signup",
        description="Volunteer cancels their registration.",
        request=None,
        responses={200: OpenApiResponse(description="Registration Cancelled")}
    )
    def delete(self, request, pk):
        event = get_object_or_404(Event, pk=pk)
        signup = get_object_or_404(EventParticipant, event=event, volunteer=request.user)
        
        signup.delete()
        return Response({"status": "Registration cancelled."}, status=status.HTTP_200_OK)