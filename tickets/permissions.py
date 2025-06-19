from django.utils import timezone
from rest_framework import permissions
from rest_framework.permissions import BasePermission
from tickets.models.ticket_setup import Ticket
from rest_framework import permissions
import jwt
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed


class IsTicketCreator(permissions.IsAuthenticated):
    def has_object_permission(self, request, view, obj: Ticket):
        return obj.created_by == request.user


class IsCreatedWithinSameDay(BasePermission):
    def has_object_permission(self, request, view, obj: Ticket):
        current_date = timezone.now().date()
        return obj.created_at.date() == current_date


class HasValidTicketToken(BasePermission):
    def has_permission(self, request, view):
        token = request.headers.get('X-Ticket-Token')
        if not token:
            raise AuthenticationFailed('No ticket token provided.')

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            return True
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('The ticket token has expired.')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid ticket token.')
