# user/email_service.py
import logging
import threading

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EmailService:
    """Unified email service using Django's SMTP backend."""
    
    @staticmethod
    def send_otp_email(user_email, otp_code):
        """Send 6-digit OTP for email verification."""
        try:
            subject = "Your Verification Code - NGOConnect"
            
            text_body = f"""
Hello,

Your verification code for NGOConnect is: {otp_code}

This code will expire in 5 minutes.

If you didn't request this code, please ignore this email.

Best regards,
NGOConnect Team
            """
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .otp-box {{ 
            font-size: 24px; 
            font-weight: bold; 
            letter-spacing: 5px; 
            color: #4CAF50; 
            background: #f4f4f4; 
            padding: 15px; 
            text-align: center; 
            margin: 20px 0; 
            border-radius: 8px;
        }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Verify Your Email</h2>
        <p>Use the following code to complete your registration:</p>
        
        <div class="otp-box">{otp_code}</div>
        
        <p>This code is valid for 5 minutes.</p>
        <div class="footer">
            <p>If you didn't create an account with us, please ignore this email.</p>
            <p>Best regards,<br>NGOConnect Team</p>
        </div>
    </div>
</body>
</html>
            """
            
            # Reuse your base send_email method
            return EmailService.send_email(user_email, subject, text_body, html_body)
            
        except Exception as e:
            logger.error(f"OTP email sending failed: {str(e)}")
            return False
    
    @staticmethod
    def _send_email_thread(to_email, subject, text_body, html_body):
        """Actual sending logic running in a thread."""
        try:
            send_mail(
                subject=subject,
                message=text_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                html_message=html_body,
                fail_silently=False,
            )
            logger.info(f"Email sent successfully to {to_email}")
        except Exception as e:
            logger.error(f"Email sending failed to {to_email}: {str(e)}")

    @staticmethod
    def send_email(to_email, subject, text_body, html_body=None):
        """Base method to send emails (Threaded)."""
        try:
            email_thread = threading.Thread(
                target=EmailService._send_email_thread,
                args=(to_email, subject, text_body, html_body)
            )
            email_thread.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start email thread for {to_email}: {str(e)}")
            return False
    
    @staticmethod
    def send_verification_email(user_email, verification_token):
        """Send email verification link to new users."""
        try:
            verification_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}&email={user_email}"
            
            subject = "Verify Your Email - NGOConnect"
            
            text_body = f"""
Hello,

Welcome to NGOConnect! Please verify your email address by clicking the link below:

{verification_link}

This link will expire in 24 hours.

If you didn't create an account with us, please ignore this email.

Best regards,
NGOConnect Team
            """
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{ 
            display: inline-block; 
            padding: 12px 24px; 
            background-color: #4CAF50; 
            color: white; 
            text-decoration: none; 
            border-radius: 4px; 
            margin: 20px 0;
        }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Welcome to NGOConnect!</h2>
        <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
        <a href="{verification_link}" class="button">Verify Email</a>
        <p>Or copy and paste this link in your browser:</p>
        <p>{verification_link}</p>
        <p>This link will expire in 24 hours.</p>
        <div class="footer">
            <p>If you didn't create an account with us, please ignore this email.</p>
            <p>Best regards,<br>NGOConnect Team</p>
        </div>
    </div>
</body>
</html>
            """
            
            return EmailService.send_email(user_email, subject, text_body, html_body)
            
        except Exception as e:
            logger.error(f"Verification email sending failed: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(user_email, reset_token):
        """Send password reset link to users."""
        try:
            reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}&email={user_email}"
            
            subject = "Reset Your Password - NGOConnect"
            
            text_body = f"""
Hello,

You requested to reset your password for your NGOConnect account. Click the link below to reset your password:

{reset_link}

This link will expire in 30 minutes for security reasons.

If you didn't request this password reset, please ignore this email.

Best regards,
NGOConnect Team
            """
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .button {{ 
            display: inline-block; 
            padding: 12px 24px; 
            background-color: #2196F3; 
            color: white; 
            text-decoration: none; 
            border-radius: 4px; 
            margin: 20px 0;
        }}
        .warning {{ color: #f44336; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Reset Your Password</h2>
        <p>You requested to reset your password. Click the button below to proceed:</p>
        <a href="{reset_link}" class="button">Reset Password</a>
        <p>Or copy and paste this link in your browser:</p>
        <p>{reset_link}</p>
        <p class="warning">This link will expire in 30 minutes.</p>
        <div class="footer">
            <p>If you didn't request this password reset, please ignore this email.</p>
            <p>Best regards,<br>NGOConnect Team</p>
        </div>
    </div>
</body>
</html>
            """
            
            return EmailService.send_email(user_email, subject, text_body, html_body)
            
        except Exception as e:
            logger.error(f"Password reset email sending failed: {str(e)}")
            return False
    
    @staticmethod
    def send_welcome_email(user_email, first_name):
        """Send welcome email after successful verification."""
        try:
            subject = "Welcome to NGOConnect!"
            
            name = first_name if first_name else "there"
            
            text_body = f"""
Hello {name},

Your email has been verified successfully. Welcome to NGOConnect!

You can now log in to your account and start exploring our platform.

Best regards,
NGOConnect Team
            """
            
            return EmailService.send_email(user_email, subject, text_body)
            
        except Exception as e:
            logger.error(f"Welcome email sending failed: {str(e)}")
            return False

    @staticmethod
    def send_donation_receipt(donation):
        """Send donation receipt email."""
        try:
            subject = "Donation Receipt - NGOConnect"
            
            donor_name = donation.donor_name or (donation.donor.first_name if donation.donor else "Valued Donor")
            amount = donation.amount
            trx_id = donation.transaction_id
            date = donation.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            campaign_title = donation.campaign.title if donation.campaign else "General Donation"
            
            text_body = f"""
Hello {donor_name},

Thank you for your generous donation of BDT {amount} for "{campaign_title}".

Transaction ID: {trx_id}
Date: {date}

Your contribution will make a significant impact.

Best regards,
NGOConnect Team
            """
            
            html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-top: 5px solid #4CAF50; }}
        .header {{ text-align: center; margin-bottom: 20px; }}
        .header h2 {{ color: #4CAF50; }}
        .receipt-box {{ background: #f9f9f9; padding: 20px; margin: 20px 0; border-radius: 5px; }}
        .amount {{ font-size: 24px; font-weight: bold; color: #333; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #666; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h2>Thank You!</h2>
            <p>Your donation has been received successfully.</p>
        </div>
        
        <p>Hello {donor_name},</p>
        <p>Thank you for your generous donation to <strong>{campaign_title}</strong>.</p>
        
        <div class="receipt-box">
            <p>Amount Donated:</p>
            <p class="amount">BDT {amount}</p>
            <hr>
            <p><strong>Transaction ID:</strong> {trx_id}</p>
            <p><strong>Date:</strong> {date}</p>
            <p><strong>Status:</strong> Success</p>
        </div>
        
        <p>Your contribution will make a significant impact.</p>
        
        <div class="footer">
            <p>NGOConnect Team</p>
            <p>This is an automated receipt.</p>
        </div>
    </div>
</body>
</html>
            """
            
            email = donation.donor_email or (donation.donor.email if donation.donor else None)
            if email:
                return EmailService.send_email(email, subject, text_body, html_body)
            return False
            
        except Exception as e:
            logger.error(f"Donation receipt email sending failed: {str(e)}")
            return False

    @staticmethod
    def send_contact_notification(sender_name, sender_email, subject, message, recipient_email):
        """Send contact us notification to admin/manager."""
        try:
            email_subject = f"New Contact Message: {subject}"
            
            text_body = f"""
New message from the Contact Us form.

Name: {sender_name}
Email: {sender_email}
Subject: {subject}

Message:
{message}
            """
            
            return EmailService.send_email(recipient_email, email_subject, text_body)
            
        except Exception as e:
            logger.error(f"Contact notification failed: {str(e)}")
            return False

    @staticmethod
    def send_volunteer_application_notification(applicant_name, applicant_email, recipient_email):
        """Notify admin/manager about a new volunteer application."""
        try:
            subject = "New Volunteer Application - NGOConnect"
            
            text_body = f"""
Hello,

A new volunteer application has been submitted.

Name: {applicant_name}
Email: {applicant_email}

Please log in to the admin panel to review the application.

Best regards,
NGOConnect Team
            """
            return EmailService.send_email(recipient_email, subject, text_body)
        except Exception as e:
            logger.error(f"Volunteer app notification failed: {str(e)}")
            return False

    @staticmethod
    def send_volunteer_status_update(applicant_email, applicant_name, new_status):
        """Notify volunteer about their application status change."""
        try:
            subject = f"Volunteer Application Update - {new_status}"
            
            message_part = ""
            if new_status == 'APPROVED':
                message_part = "Congratulations! Your application has been approved. You can now log in and access the volunteer dashboard."
            elif new_status == 'REJECTED':
                message_part = "Thank you for your interest. Unfortunately, your application has been declined at this time."
            else:
                message_part = f"Your application status has been updated to: {new_status}"

            text_body = f"""
Hello {applicant_name},

{message_part}

Best regards,
NGOConnect Team
            """
            return EmailService.send_email(applicant_email, subject, text_body)
        except Exception as e:
            logger.error(f"Volunteer status update email failed: {str(e)}")
            return False


# Backward compatibility alias
class PasswordResetEmailService:
    @staticmethod
    def send_reset_email(user_email, reset_token):
        return EmailService.send_password_reset_email(user_email, reset_token)