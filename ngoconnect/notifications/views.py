from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List My Notifications",
        description="Get a list of all notifications for the logged-in user.",
        responses={200: NotificationSerializer(many=True)}
    )
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)

class NotificationMarkReadView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Mark Notification as Read",
        description="Update the is_read status of a notification.",
        responses={200: NotificationSerializer}
    )
    def patch(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.is_read = True
        notification.save()
        serializer = NotificationSerializer(notification)
        return Response(serializer.data)

class NotificationMarkAllReadView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Mark All as Read",
        description="Mark all notifications for the user as read.",
        responses={200: OpenApiResponse(description="Success")}
    )
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"message": "All marked as read"}, status=status.HTTP_200_OK)
