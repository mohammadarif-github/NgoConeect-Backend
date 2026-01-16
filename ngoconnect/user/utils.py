# utils.py
import base64
from io import BytesIO
from urllib.parse import urlencode

import pyotp
import qrcode
import requests
from django.conf import settings
from django.core.mail import send_mail


def send_password_reset_email(email, token, frontend_url="http://localhost:3000"):
    """
    Sends password reset link.
    frontend_url should be your actual frontend in production.
    """
    reset_link = f"{frontend_url}/reset-password?token={token}"
    
    subject = 'Password Reset Request'
    message = f'''
You requested to reset your password.

Click the link below to reset your password:
{reset_link}

This link expires in 1 hour.

If you didn't request this, please ignore this email.
'''
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )    

def get_google_auth_url():
    """
    Generate Google OAuth URL.
    User will be redirected to this URL to login with Google.
    """
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'scope': 'email profile',
        'response_type': 'code',
        'access_type': 'offline',  # Get refresh token
        'prompt': 'select_account',  # Always show account picker
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"


def exchange_google_code(code):
    """
    Exchange authorization code for tokens.
    
    Args:
        code: The authorization code from Google callback
        
    Returns:
        dict: Contains access_token, refresh_token, etc.
        None: If exchange failed
    """
    response = requests.post(
        'https://oauth2.googleapis.com/token',
        data={
            'code': code,
            'client_id': settings.GOOGLE_CLIENT_ID,
            'client_secret': settings.GOOGLE_CLIENT_SECRET,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'grant_type': 'authorization_code',
        },
        timeout=10
    )
    
    if response.status_code == 200:
        return response.json()
    return None


def get_google_user_info(access_token):
    """
    Get user info from Google using access token.
    
    Args:
        access_token: Google access token
        
    Returns:
        dict: User info (email, name, picture, etc.)
        None: If request failed
    """
    response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {access_token}'},
        timeout=10
    )
    
    if response.status_code == 200:
        return response.json()
    return None

