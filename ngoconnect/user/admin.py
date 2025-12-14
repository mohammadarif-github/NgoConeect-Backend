from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active',"is_email_verified"]
    list_filter = ['role', 'is_staff', 'is_active', 'is_google_user']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'is_email_verified')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Google Auth', {'fields': ('google_id', 'is_google_user')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'first_name', 'last_name', 'role'),
        }),
    )
    search_fields = ['email', 'first_name', 'last_name']

admin.site.register(User, UserAdmin)
