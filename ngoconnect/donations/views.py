# donations/views.py
import logging
from datetime import datetime

import pandas as pd
from core.permissions import IsAdminOrReadOnly
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import (
    OpenApiParameter, OpenApiResponse, extend_schema,
)
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
            if validation_response and (validation_response.get('status') == 'VALID' or validation_response.get('status') == 'VALIDATED'):
                donation.status = 'SUCCESS'
                donation.payment_gateway_response = validation_response or {}
                donation.save()
                
                # Send Receipt
                if not donation.receipt_sent:
                    if EmailService.send_donation_receipt(donation):
                        donation.receipt_sent = True
                        donation.save()
                        
                # Update Campaign Collected Amount
                if donation.campaign:
                    # Using F() expression to avoid race conditions
                    from django.db.models import F
                    donation.campaign.current_amount = F('current_amount') + donation.amount
                    donation.campaign.save()
                    donation.campaign.refresh_from_db() # Refresh to get the actual value if needed elsewhere

                # Upgrade Role: If user is general_user, upgrade to 'donor'
                if donation.donor and donation.donor.role == 'general_user':
                    donation.donor.role = 'donor'
                    donation.donor.save(update_fields=['role'])

                return redirect(f"{settings.FRONTEND_URL}/donation_success/?tran_id={tran_id}") # Redirect to Frontend Success Page
            else:
                donation.status = 'FAILED'
                donation.payment_gateway_response = validation_response or {}
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


class ExportDonationsView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Export Donations CSV",
        description="Export donation records as CSV. Admin/Manager only.",
        parameters=[
            OpenApiParameter(name='campaign_id', description='Filter by Campaign ID', required=False, type=int),
            OpenApiParameter(name='start_date', description='Start Date (YYYY-MM-DD)', required=False, type=str),
            OpenApiParameter(name='end_date', description='End Date (YYYY-MM-DD)', required=False, type=str),
        ],
        responses={200: OpenApiResponse(description="CSV File Download")}
    )
    def get(self, request):
        if request.user.role not in ['admin', 'manager']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        donations = Donation.objects.all().order_by('-timestamp')

        # Filters
        campaign_id = request.query_params.get('campaign_id')
        if campaign_id:
            donations = donations.filter(campaign_id=campaign_id)
        
        start_date = request.query_params.get('start_date')
        if start_date:
            try:
                # Parse date assuming inputs are naive dates, converting to aware start of day
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                start_dt = timezone.make_aware(start_dt)
                donations = donations.filter(timestamp__gte=start_dt)
            except ValueError:
                pass

        end_date = request.query_params.get('end_date')
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                end_dt = end_dt.replace(hour=23, minute=59, second=59)
                end_dt = timezone.make_aware(end_dt)
                donations = donations.filter(timestamp__lte=end_dt)
            except ValueError:
                pass

        # Prepare data for Pandas
        data = []
        for d in donations:
            if d.donor:
                donor_name = f"{d.donor.first_name} {d.donor.last_name}".strip() or "Unknown"
                donor_email = d.donor.email
            else:
                donor_name = d.donor_name
                donor_email = d.donor_email
            
            campaign_title = d.campaign.title if d.campaign else "General Fund"
            
            data.append({
                'Donation ID': d.id,
                'Transaction ID': d.transaction_id,
                'Date': d.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'Amount': d.amount,
                'Status': d.status,
                'Donor Name': donor_name,
                'Donor Email': donor_email,
                'Campaign': campaign_title,
            })
            
        if not data:
            # If no data, still return a CSV with headers or empty message? 
            # Usually better to return an empty CSV or 404. Let's return empty CSV with headers.
            df = pd.DataFrame(columns=['Donation ID', 'Transaction ID', 'Date', 'Amount', 'Status', 'Donor Name', 'Donor Email', 'Campaign'])
        else:
            df = pd.DataFrame(data)
        
        response = HttpResponse(content_type='text/csv')
        filename = f"donations_export_{timezone.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        df.to_csv(path_or_buf=response, index=False)
        return response

