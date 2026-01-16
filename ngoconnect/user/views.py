# user/views.py
import structlog
from core.permissions import IsBusinessAdmin
from django.db import transaction
from donations.models import Donation
from donations.serializers import DonationPublicSerializer
from drf_spectacular.openapi import OpenApiResponse
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView, TokenRefreshView as BaseTokenRefreshView,
)

from .email_service import EmailService
from .models import EmailOtp, EmailVerificationToken, PasswordResetToken, User
from .serializers import (
    AdminPasswordResetSerializer, ChangePasswordSerializer,
    CustomTokenObtainPairSerializer, DonationHistorySerializer,
    ForgotPasswordSerializer, LogoutSerializer, ResendOtpSerializer,
    ResetPasswordSerializer, TokenRefreshResponseSerializer,
    TokenRefreshSerializer, UserCreateSerializer, UserListSerializer,
    UserProfileSerializer, UserUpdateSerializer, VerifyEmailSerializer,
)

logger = structlog.get_logger("api.business")
security_logger = structlog.get_logger("api.security")
audit_logger = structlog.get_logger("api.audit")


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class TokenRefreshView(BaseTokenRefreshView):
    @extend_schema(
        request=TokenRefreshSerializer,
        responses={200: TokenRefreshResponseSerializer},
        summary="Refresh JWT Token"
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class RegistrationView(APIView):
    """
    Public endpoint for user registration.
    Creates user and sends 6-digit verification code.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'email_apis'

    @extend_schema(
        summary="Register new user",
        description="Register a new user and send an email with a 6-digit verification code (OTP).",
        request=UserCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="User registered successfully",
                examples=[
                    OpenApiExample(
                        'Success',
                        value={
                            'message': 'Registration successful. Please check your email for the OTP.',
                            'email': 'user@example.com'
                        }
                    )
                ]
            ),
            400: OpenApiResponse(description="Validation errors or User already exists"),
            500: OpenApiResponse(description="Email sending failed")
        }
    )
    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # 1. Create User (Active=False until verified)
                    user = serializer.save()
                    
                    # 2. Generate OTP
                    otp_instance = EmailOtp.objects.create(user=user)
                    
                    # 3. Send Email
                    if EmailService.send_otp_email(user.email, otp_instance.otp):
                        return Response({
                            'message': 'Registration successful. Please check your email for the OTP.',
                            'email': user.email
                        }, status=status.HTTP_201_CREATED)
                    else:
                        # User created, but email failed. 
                        # We don't rollback user creation here so they can use "Resend OTP" logic,
                        # but you could raise an exception to rollback if preferred.
                        return Response({
                            'message': 'User registered, but failed to send email. Please use the Resend OTP endpoint.',
                            'email': user.email
                        }, status=status.HTTP_201_CREATED)
                        
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """
    Public endpoint to verify user email using OTP.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'email_apis'

    @extend_schema(
        summary="Verify Email OTP",
        description="Verify the user's email address using the 6-digit OTP sent to their email.",
        request=VerifyEmailSerializer,
        responses={
            200: OpenApiResponse(
                description="Email verified successfully",
                examples=[
                    OpenApiExample(
                        'Success',
                        value={'message': 'Email verified successfully! You can now login.'}
                    )
                ]
            ),
            400: OpenApiResponse(description="Invalid OTP, Expired OTP, or Missing fields"),
            404: OpenApiResponse(description="User not found")
        }
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        if user.is_email_verified:
            return Response({'message': 'Email already verified'}, status=status.HTTP_200_OK)

        # Get latest OTP
        try:
            otp_record = EmailOtp.objects.filter(user=user).latest('created_at')
        except EmailOtp.DoesNotExist:
            return Response({'error': 'No OTP found. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

        # OTP Validation
        if otp_record.otp != otp_code:
            otp_record.attempts += 1
            otp_record.save()
            return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_record.is_expired():
            return Response({'error': 'OTP has expired'}, status=status.HTTP_400_BAD_REQUEST)

        if otp_record.attempts >= 5:
            return Response({'error': 'Too many failed attempts. Request a new OTP.'}, status=status.HTTP_400_BAD_REQUEST)

        # Success Logic
        user.is_active = True
        user.is_email_verified = True
        user.save()
        
        # Cleanup
        EmailOtp.objects.filter(user=user).delete()
        
        # Send Welcome Email (Optional, non-blocking)
        try:
            EmailService.send_welcome_email(user.email, user.first_name)
        except:
            pass #nosec

        return Response({'message': 'Email verified successfully! You can now login.'}, status=status.HTTP_200_OK)


class ResendOtpView(APIView):
    """
    Public endpoint to resend OTP if the previous one expired or was lost.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'email_apis'

    @extend_schema(
        summary="Resend OTP",
        description="Generate and send a new OTP to the user's email.",
        request=ResendOtpSerializer,
        responses={
            200: OpenApiResponse(
                description="OTP sent successfully",
                examples=[
                    OpenApiExample(
                        'Success',
                        value={'message': 'New OTP sent successfully'}
                    )
                ]
            ),
            404: OpenApiResponse(description="User not found")
        }
    )
    def post(self, request):
        serializer = ResendOtpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            if user.is_email_verified:
                return Response({'message': 'User is already verified'}, status=status.HTTP_200_OK)
            
            # Generate New OTP
            otp_instance = EmailOtp.objects.create(user=user)
            
            # Send Email
            if EmailService.send_otp_email(user.email, otp_instance.otp):
                return Response({'message': 'New OTP sent successfully'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Failed to send email. Try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get user profile",
        description="Retrieve the current user's profile information",
        responses={200: UserProfileSerializer}
    )
    def get(self, request):
        logger.info(f"Profile accessed by user {request.user.email}")
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Update user profile",
        description="Update user's first name and/or last name",
        request=UserUpdateSerializer,
        responses={200: UserProfileSerializer}
    )
    def patch(self, request):
        if 'is_active' in request.data and not request.data['is_active']:
            can_proceed, error_message = request.user.can_be_deactivated_or_deleted()
            if not can_proceed:
                return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            old_data = f"{request.user.first_name} {request.user.last_name}"
            serializer.save()
            new_data = f"{request.user.first_name} {request.user.last_name}"
            audit_logger.info(f"Profile updated by {request.user.email}: '{old_data}' -> '{new_data}'")
            return Response(UserProfileSerializer(request.user).data)
        
        logger.warning(f"Profile update failed for {request.user.email} - validation errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'post_apis'
    
    @extend_schema(
        summary="Change password",
        description="Change the current user's password",
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password changed successfully"),
            400: OpenApiResponse(description="Invalid password or validation errors")
        }
    )
    def post(self, request):
        user_email = request.user.email
        security_logger.info(f"Password change attempt for user {user_email}")
        
        serializer = ChangePasswordSerializer(
            data=request.data, 
            context={'user': request.user}
        )
        if serializer.is_valid():
            if not request.user.check_password(serializer.validated_data['old_password']):
                security_logger.warning(f"Password change failed for {user_email} - invalid old password")
                return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
            
            request.user.set_password(serializer.validated_data['new_password'])
            request.user.save()
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDonationHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="My Donation History",
        description="List all donations made by the logged-in user.",
        responses={200: DonationHistorySerializer(many=True)}
    )
    def get(self, request):
        donations = Donation.objects.filter(donor=request.user).order_by('-timestamp')
        serializer = DonationHistorySerializer(donations, many=True)
        return Response(serializer.data)



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Logout user",
        description="Logout user by blacklisting refresh token",
        request=LogoutSerializer,
        responses={
            200: OpenApiResponse(description="Logout successful"),
            400: OpenApiResponse(description="Invalid token")
        }
    )
    def post(self, request):
        user_email = getattr(request.user, 'email', 'unknown')
        
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Logout failed for {user_email} - invalid data")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            refresh_token = serializer.validated_data['refresh']
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            logger.info(f"User {user_email} logged out successfully")
            return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
            
        except TokenError as e:
            error_message = str(e).lower()
            
            if any(word in error_message for word in ['blacklisted', 'expired']):
                logger.info(f"User {user_email} logout - refresh token already invalid: {str(e)}")
                return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
            else:
                logger.warning(f"User {user_email} logout failed - invalid refresh token: {str(e)}")
                return Response({'error': 'Invalid refresh token provided'}, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Unexpected logout error for {user_email}: {str(e)}")
            return Response({'error': 'An error occurred during logout'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'email_apis'
    
    @extend_schema(
        summary="Request password reset",
        description="Send a password reset email to the user",
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password reset email sent"),
            400: OpenApiResponse(description="Validation errors")
        }
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            security_logger.warning(f"Password reset request failed - validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        email = serializer.validated_data['email']
        security_logger.info(f"Password reset requested for email: {email}")
        
        try:
            user = User.objects.get(email=email)
            
            # Invalidate existing tokens
            PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
            
            # Create new token
            reset_token = PasswordResetToken.objects.create(user=user)
            
            # Send email
            email_sent = EmailService.send_password_reset_email(email, reset_token.token)
            
            if email_sent:
                security_logger.info(f"Password reset email sent successfully to {email}")
            else:
                security_logger.error(f"Failed to send password reset email to {email}")
                
        except User.DoesNotExist:
            security_logger.warning(f"Password reset requested for non-existent email: {email}")
        
        # Always return success (security - don't reveal if email exists)
        return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Reset password with token",
        description="Reset user password using the token received via email",
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description="Password reset successfully"),
            400: OpenApiResponse(description="Invalid or expired token")
        }
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        
        if not serializer.is_valid():
            security_logger.warning(f"Password reset failed - validation errors: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        token = serializer.validated_data['token']
        email = serializer.validated_data['email']
        new_password = serializer.validated_data['new_password']
        
        try:
            user = User.objects.get(email=email)
            reset_token = PasswordResetToken.objects.get(token=token, user=user)
            
            if not reset_token.is_valid:
                security_logger.warning(f"Password reset failed for {email} - expired or invalid token")
                return Response(
                    {'error': 'Token is expired or invalid'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.set_password(new_password)
            user.save()
            
            reset_token.is_used = True
            reset_token.save()
            
            security_logger.info(f"Password reset completed successfully for user {email}")
            return Response({'message': 'Password reset successfully'}, status=status.HTTP_200_OK)
            
        except (User.DoesNotExist, PasswordResetToken.DoesNotExist):
            security_logger.warning(f"Password reset failed for {email} - invalid token or email")
            return Response({'error': 'Invalid token or email'}, status=status.HTTP_400_BAD_REQUEST)


# Admin Views
class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessAdmin]
    
    @extend_schema(
        summary="List all users (Admin only)",
        description="Get list of all users in the system",
        responses={200: UserListSerializer(many=True)}
    )
    def get(self, request):
        users = User.objects.all().order_by('first_name', 'last_name')
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)


class AdminUserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessAdmin]
    
    def get_object(self, user_id):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
    
    @extend_schema(
        summary="Get user details (Admin only)",
        description="Get detailed information about a specific user",
        responses={200: UserListSerializer, 404: OpenApiResponse(description="User not found")}
    )
    def get(self, request, user_id):
        user = self.get_object(user_id)
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserListSerializer(user)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Update user (Admin only)",
        description="Admin can update user's name, role, and active status",
        request=UserUpdateSerializer,
        responses={200: UserListSerializer, 404: OpenApiResponse(description="User not found")}
    )
    def patch(self, request, user_id):
        user = self.get_object(user_id)
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = UserUpdateSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserListSerializer(user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        summary="Delete user (Admin only)",
        description="Admin can delete a user from the system",
        responses={200: OpenApiResponse(description="User deleted successfully"), 404: OpenApiResponse(description="User not found")}
    )
    def delete(self, request, user_id):
        user = self.get_object(user_id)
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        can_proceed, error_message = user.can_be_deactivated_or_deleted()
        if not can_proceed:
            return Response({'error': error_message}, status=status.HTTP_400_BAD_REQUEST)
        
        user_email = user.email
        user.delete()
        
        return Response({'message': f'User {user_email} deleted successfully'}, status=status.HTTP_200_OK)


class AdminResetPasswordView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessAdmin]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'post_apis'
    
    @extend_schema(
        summary="Reset user password (Admin only)",
        description="Admin can reset any user's password",
        request=AdminPasswordResetSerializer,
        responses={
            200: OpenApiResponse(description="Password reset successfully"),
            404: OpenApiResponse(description="User not found")
        }
    )
    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = AdminPasswordResetSerializer(data=request.data, context={'user': user})
        if serializer.is_valid():
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password reset successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)