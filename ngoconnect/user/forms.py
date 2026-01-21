# user/forms.py
from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.password_validation import (
    password_validators_help_text_html,
)

from .models import User


class CustomUserCreationForm(UserCreationForm):
    # Overriding the parent fields to ensure they have the correct attributes if needed,
    # or we could just rely on the parent. But let's match the parent's field names: password1 and password2.
    # Note: Django's UserCreationForm uses 'password1' and 'password2' (no underscores).
    
    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "role", "password1", "password2")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"