# donations/views.py
import logging

from core.permissions import IsAdminOrReadOnly
from django.conf import settings
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import OpenApiResponse, extend_schema
from projects.models import Campaign
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from user.email_service import EmailService

from .models import Donation
from .serializers import (
    DonationAdminSerializer, DonationInitiateSerializer,
    DonationPublicSerializer,
)
from .utils import SSLCommerzService

logger = logging.getLogger(__name__)

class InitiateDonationView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Initiate Donation",
        description="Start a donation process. Returns SSLCommerz Gateway URL.",
        request=DonationInitiateSerializer,
        responses={
            200: OpenApiResponse(description="Payment URL generated", response={'payment_url': 'https://sandbox...'})
        }
    )
    def post(self, request):
        serializer = DonationInitiateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            data = serializer.validated_data
            
            # Create Donation Record (Pending)
            donation = Donation(
                amount=data['amount'],
                status='PENDING'
            )
            
            if 'campaign_id' in data and data['campaign_id']:
                try:
                    donation.campaign = Campaign.objects.get(id=data['campaign_id'])
                except Campaign.DoesNotExist:
                    pass
            
            if request.user.is_authenticated:
                donation.donor = request.user
                donation.donor_email = request.user.email
                donation.donor_name = f"{request.user.first_name} {request.user.last_name}"
            else:
                donation.donor_email = data['guest_email']
                donation.donor_name = data['guest_name']
                
            donation.save() # Generates ID, we might need it for transaction_id logic if we used ID
            
            # Initiate Payment
            ssl_service = SSLCommerzService()
            response = ssl_service.initiate_payment(donation, user_details={
                'name': donation.donor_name,
                'email': donation.donor_email
            })
            
            if response['status'] == 'SUCCESS':
                donation.payment_gateway_response = response
                donation.save()
                return Response({'payment_url': response['GatewayPageURL'], 'sessionkey': response['sessionkey']})
            else:
                return Response({'error': 'Failed to initiate payment gateway', 'details': response}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class PaymentSuccessView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(exclude=True)
    def post(self, request):
        data = request.POST
        val_id = data.get('val_id')
        tran_id = data.get('tran_id')
        
        try:
            donation = Donation.objects.get(transaction_id=tran_id)
        except Donation.DoesNotExist:
             return Response({'error': 'Transaction not found'}, status=status.HTTP_404_NOT_FOUND)

        # Validate with SSLCommerz to be sure
        ssl_service = SSLCommerzService()
        if val_id:
            validation_response = ssl_service.validate_payment(val_id)
            if validation_response['status'] == 'VALID' or validation_response['status'] == 'VALIDATED':
                donation.status = 'SUCCESS'
                donation.payment_gateway_response = validation_response
                donation.save()
                
                # Send Receipt
                if not donation.receipt_sent:
                    if EmailService.send_donation_receipt(donation):
                        donation.receipt_sent = True
                        donation.save()
                        
                # Update Campaign Collected Amount (Optional but good)
                # if donation.campaign:
                #     donation.campaign.amount_collected += donation.amount
                #     donation.campaign.save()

                return redirect(f"{settings.FRONTEND_URL}/donation_success/?tran_id={tran_id}") # Redirect to Frontend Success Page
            else:
                donation.status = 'FAILED'
                donation.payment_gateway_response = validation_response
                donation.save()
                return redirect(f"{settings.FRONTEND_URL}/donation_fail/?tran_id={tran_id}")
        
        return Response({'error': 'No validation ID provided'}, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class PaymentFailView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(exclude=True)
    def post(self, request):
        data = request.POST
        tran_id = data.get('tran_id')
        if tran_id:
             try:
                donation = Donation.objects.get(transaction_id=tran_id)
                donation.status = 'FAILED'
                donation.payment_gateway_response = data
                donation.save()
             except Donation.DoesNotExist:
                pass
        return redirect(f"{settings.FRONTEND_URL}/donation_fail/?tran_id={tran_id}")

@method_decorator(csrf_exempt, name='dispatch')
class PaymentCancelView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(exclude=True)
    def post(self, request):
        data = request.POST
        tran_id = data.get('tran_id')
        if tran_id:
             try:
                donation = Donation.objects.get(transaction_id=tran_id)
                donation.status = 'FAILED' # Or CANCELLED
                donation.payment_gateway_response = data
                donation.save()
             except Donation.DoesNotExist:
                pass
        return redirect(f"{settings.FRONTEND_URL}/donation_cancel/?tran_id={tran_id}")


class PublicDonationListView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Recent Donations",
        description="Public list of recent successful donations for transparency.",
        responses={200: DonationPublicSerializer(many=True)}
    )
    def get(self, request):
        # Show last 20 successful donations
        donations = Donation.objects.filter(status='SUCCESS').order_by('-timestamp')[:20]
        serializer = DonationPublicSerializer(donations, many=True)
        return Response(serializer.data)


class AdminDonationListView(APIView):
    permission_classes = [IsAuthenticated] # Needs finer permission: IsAdminOrManager
    
    @extend_schema(
        summary="All Donations (Admin)",
        description="Full list of donations with details (Admin/Manager only).",
        responses={200: DonationAdminSerializer(many=True)}
    )
    def get(self, request):
        if request.user.role not in ['admin', 'manager']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
        donations = Donation.objects.all().order_by('-timestamp')
        
        # Filters
        campaign_id = request.query_params.get('campaign_id')
        if campaign_id:
            donations = donations.filter(campaign_id=campaign_id)
            
        status_param = request.query_params.get('status')
        if status_param:
            donations = donations.filter(status=status_param.upper())

        serializer = DonationAdminSerializer(donations, many=True)
        return Response(serializer.data)
