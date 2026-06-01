# ============================================================
# AI Interview System — Custom Permissions
# File: core/permissions.py
# ============================================================

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == "admin"
        )


class IsHR(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == "hr"
        )


class IsCandidate(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == "candidate"
        )


class IsAdminOrHR(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in ("admin", "hr")
        )
    
# Add this to core/permissions.py

class IsOwnerOrHR(BasePermission):
    """
    Object-level permission to allow candidates to edit their own data,
    but allow HR to view everything.
    """
    def has_object_permission(self, request, view, obj):
        # HR and Admin always have access
        if request.user.role in ['hr', 'admin']:
            return True
        
        # Check if the object belongs to the user (works for Profile, Application, etc.)
        # This assumes the model has a 'user' or 'candidate' field
        return getattr(obj, 'user', None) == request.user or \
               getattr(obj, 'candidate', None) == request.user