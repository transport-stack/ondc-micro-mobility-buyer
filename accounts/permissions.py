from rest_framework import permissions


class IsUserOwner(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, user):
        return user == request.user
