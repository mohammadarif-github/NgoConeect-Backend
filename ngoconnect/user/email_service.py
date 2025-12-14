# user/email_service.py
import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EmailService:
    """Unified email service using Django's SMTP backend."""
    
    @staticmethod
    def send_email(to_email, subject, text_body, html_body=None):
        """Base method to send emails."""
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
            return True
        except Exception as e:
            logger.error(f"Email sending failed to {to_email}: {str(e)}")
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


# Backward compatibility alias
class PasswordResetEmailService:
    @staticmethod
    def send_reset_email(user_email, reset_token):
        return EmailService.send_password_reset_email(user_email, reset_token)