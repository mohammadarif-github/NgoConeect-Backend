# user/serializers.py
import logging

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User

logger = logging.getLogger(__name__)


class TokenRefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    
    class Meta:
        ref_name = 'TokenRefresh'
        

class TokenRefreshResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    
    class Meta:
        ref_name = 'TokenRefreshResponse'


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        return token
    
    def validate(self, attrs):
        email = attrs.get('email') or attrs.get('username')
        password = attrs.get('password')
        
        logger.info(f"Login attempt for email: {email}")
        
        # Step 1: Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            logger.warning(f"Login failed - user not found: {email}")
            raise serializers.ValidationError("User with this email doesn't exist")
        
        # Step 2: Check if email is verified
        if not user.is_email_verified:
            logger.warning(f"Login failed - email not verified: {email}")
            raise serializers.ValidationError("Please verify your email before logging in.")
        
        # Step 3: Check if account is active
        if not user.is_active:
            logger.warning(f"Login failed - inactive account: {email}")
            raise serializers.ValidationError("Your account has been deactivated. Please contact support.")
        
        # Step 4: Check password
        authenticated_user = authenticate(username=email, password=password)
        if authenticated_user is None:
            logger.warning(f"Login failed - wrong password: {email}")
            raise serializers.ValidationError("Your password is incorrect")
        
        logger.info(f"Login successful for: {email}")
        data = super().validate(attrs)
        return data


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(
        required=True,
        help_text="Refresh token to blacklist"
    )
    
    def validate_refresh(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Refresh token cannot be empty")
        return value.strip()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_email_verified')
        read_only_fields = ('id', 'email', 'role', 'is_email_verified')


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("New passwords don't match")
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError("New password must be different from the old password")
        return attrs
    
    def validate_new_password(self, value):
        try:
            validate_password(value, user=self.context.get('user'))
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password', 'confirm_password') 
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_password(self, value):
        try:
            validate_password(value, user=None)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        
        # Create user with is_active=True but is_email_verified=False
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.is_email_verified = False  # Require email verification
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'role', 'is_active')
    
    def validate(self, attrs):
        """Validate that we don't deactivate the last admin"""
        user = self.instance
        
        if 'is_active' in attrs and not attrs['is_active'] and user.role == 'admin':
            can_proceed, error_message = user.can_be_deactivated_or_deleted()
            if not can_proceed:
                raise serializers.ValidationError({'is_active': error_message})
        
        if 'role' in attrs and attrs['role'] != 'admin' and user.role == 'admin':
            other_active_admins = User.objects.filter(
                role='admin',
                is_active=True
            ).exclude(id=user.id).count()
            
            if other_active_admins == 0:
                raise serializers.ValidationError({
                    'role': "Cannot change role of the last admin user. At least one admin must remain in the system."
                })
        
        return attrs


class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role', 'is_active', 'is_email_verified', 'date_joined', 'last_login')
        read_only_fields = ('id', 'date_joined', 'last_login')


class AdminPasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        min_length=8,
        write_only=True,
        help_text="New password (minimum 8 characters)"
    )
    confirm_password = serializers.CharField(
        write_only=True,
        help_text="Confirm the new password"
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_new_password(self, value):
        user = self.context.get('user')
        try:
            validate_password(value, user)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        help_text="Email address to send password reset link to"
    )


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True,
        help_text="Password reset token from email"
    )
    email = serializers.EmailField(
        required=True,
        help_text="Email address of the user"
    )
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        write_only=True,
        help_text="New password (minimum 8 characters)"
    )
    confirm_password = serializers.CharField(
        required=True,
        write_only=True,
        help_text="Confirm the new password"
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def validate_new_password(self, value):
        try:
            validate_password(value, user=None)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(
        required=True,
        help_text="Email verification token"
    )
    email = serializers.EmailField(
        required=True,
        help_text="Email address to verify"
    )


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        help_text="Email address to resend verification link"
    )