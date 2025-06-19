from rest_framework import permissions

from journey.models import Journey


class IsJourneyCreator(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj: Journey):
        return obj.created_by == request.user
