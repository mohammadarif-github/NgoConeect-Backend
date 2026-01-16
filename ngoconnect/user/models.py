# user/models.py
import secrets
from datetime import timedelta

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom manager to handle email as the unique identifier."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin') 
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_email_verified', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('volunteer', 'Volunteer'),
        ('donor', 'Donor'),
        ('manager', 'Manager'),
        ('admin', 'Admin'),
        ('general_user', 'General User'),
    ]
    
    username = None
    email = models.EmailField(unique=True, db_index=True, max_length=255)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='general_user')
    is_email_verified = models.BooleanField(default=False)  # NEW FIELD
    
    google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    is_google_user = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return self.email
    
    def can_be_deactivated_or_deleted(self):
        """Check if this user can be deactivated or deleted."""
        if self.role != 'admin':
            return True, None
        
        other_active_admins = User.objects.filter(
            role='admin',
            is_active=True
        ).exclude(id=self.id).count()
        
        if other_active_admins == 0:
            return False, "Cannot deactivate or delete the last admin user. At least one admin must remain in the system."
        
        return True, None


class EmailVerificationToken(models.Model):
    """Token for email verification during registration."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['token']),
        ]
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)  # 24 hours to verify
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
    
    def __str__(self):
        return f"Email verification token for {self.user.email}"


class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=30)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
    
    def __str__(self):
        return f"Password reset token for {self.user.email}"
    
class EmailOtp(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveIntegerField(default=0)
    
    def save(self, *args, **kwargs):
        if not self.otp:
            # Generate 6-digit secure OTP
            self.otp = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=5)
        super().save(*args, **kwargs)
        
    def is_expired(self):
        return timezone.now() >= self.expires_at
    
    def is_valid(self, otp):
        return timezone.now() < self.expires_at and self.attempts < 5
    
    def __str__(self):
        return f"{self.user.email} - {self.otp}"