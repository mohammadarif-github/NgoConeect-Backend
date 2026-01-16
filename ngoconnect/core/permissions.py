from rest_framework import permissions
from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser
    
class IsBusinessAdmin(BasePermission):
    """For business admin (role=admin) - user management, business operations"""
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'admin'
        )

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Allows read access to anyone.
    Allows write (create/edit/delete) only to Admins/Managers.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role in ['admin', 'manager']

class IsAdminOrManager(permissions.BasePermission):
    """
    Strictly for Admins/Managers (e.g., creating tasks).
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'manager']

class IsVolunteerOrAdmin(permissions.BasePermission):
    """
    Admins: Full access.
    Volunteers: Can read tasks or update tasks assigned to them.
    Others: No access.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in ['admin', 'manager', 'volunteer']

    def has_object_permission(self, request, view, obj):
        if request.user.role in ['admin', 'manager']:
            return True
        return request.user.role == 'volunteer'