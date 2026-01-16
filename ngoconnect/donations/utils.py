import uuid

from django.conf import settings
from sslcommerz_lib.sslcommerz import SSLCOMMERZ


class SSLCommerzService:
    def __init__(self):
        self.sslcz = SSLCOMMERZ({
            'store_id': settings.SSLCOMMERZ_STORE_ID,
            'store_pass': settings.SSLCOMMERZ_STORE_PASS,
            'issandbox': settings.SSLCOMMERZ_IS_SANDBOX,
        })

    def initiate_payment(self, donation_instance, user_details=None):
        """
        Initiates a payment session with SSLCommerz.
        """
        # Generate a unique transaction ID if not already present
        if not donation_instance.transaction_id:
            donation_instance.transaction_id = str(uuid.uuid4())
            donation_instance.save()
            
        post_body = {
            'total_amount': float(donation_instance.amount),
            'currency': "BDT",
            'tran_id': donation_instance.transaction_id,
            'success_url': f"{settings.FRONTEND_URL}/api/donations/payment/success/", # Adjusted for backend handling usually, but here likely calling an API
            'fail_url': f"{settings.FRONTEND_URL}/api/donations/payment/fail/",
            'cancel_url': f"{settings.FRONTEND_URL}/api/donations/payment/cancel/",
            'emi_option': 0,
            'cus_name': donation_instance.donor_name or (user_details.get('name') if user_details else 'Guest'),
            'cus_email': donation_instance.donor_email or (user_details.get('email') if user_details else 'guest@example.com'),
            'cus_phone': "01700000000", # Placeholder or from user profile
            'cus_add1': "Dhaka",
            'cus_city': "Dhaka",
            'cus_country': "Bangladesh",
            'shipping_method': "NO",
            'multi_card_name': "",
            'num_of_item': 1,
            'product_name': "Donation",
            'product_category': "Donation",
            'product_profile': "general",
        }
        
        # Override URLs if we want the backend to handle the POST return directly
        # Usually SSLCommerz expects a POST to these URLs. 
        # For an API-based backend, these should point to the Frontend which then calls the backend 
        # OR point to the Backend API directly (which then redirects to frontend).
        # Let's point to Backend API directly for processing, then Backend Redirects.
        
        backend_base = "http://localhost:8000" if settings.DEBUG else settings.BACKEND_URL 
        # Assuming we have a BACKEND_URL setting, or default to localhost for dev
        
        post_body['success_url'] = f"{backend_base}/api/donations/payment/success/?tran_id={donation_instance.transaction_id}"
        post_body['fail_url'] = f"{backend_base}/api/donations/payment/fail/?tran_id={donation_instance.transaction_id}"
        post_body['cancel_url'] = f"{backend_base}/api/donations/payment/cancel/?tran_id={donation_instance.transaction_id}"

        response = self.sslcz.createSession(post_body)
        return response

    def validate_payment(self, val_id):
        """
        Validates the payment using val_id.
        """
        return self.sslcz.validationTransactionOrder(val_id)
