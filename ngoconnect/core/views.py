from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from user.email_service import EmailService
from user.models import User

from .serializers import ContactMessageSerializer


class ContactUsView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Submit Contact Message",
        description="Public endpoint for users to send messages. Emails are sent to Admins/Managers.",
        request=ContactMessageSerializer,
        responses={201: OpenApiResponse(description="Message sent successfully")}
    )
    def post(self, request):
        serializer = ContactMessageSerializer(data=request.data)
        if serializer.is_valid():
            contact_msg = serializer.save()
            
            # Send email notifications
            admins_and_managers = User.objects.filter(role__in=['admin', 'manager'], is_active=True).values_list('email', flat=True)
            
            # Sending individually or as BCC?
            # send_email method in EmailService takes a single recipient, loop through them.
            # Ideally this should be a Celery task for performance, but straightforward loop is fine for now.
            for admin_email in admins_and_managers:
                EmailService.send_contact_notification(
                    sender_name=contact_msg.name,
                    sender_email=contact_msg.email,
                    subject=contact_msg.subject,
                    message=contact_msg.message,
                    recipient_email=admin_email
                )

            return Response({"message": "Your message has been received. We will contact you shortly."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
