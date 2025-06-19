import logging

from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import BasePermission


SERVICE_TYPE_AUTO_STR = "AUTO_RICKSHAW"
SERVICE_TYPE_CAB_STR = "CAB"
SERVICE_TYPE_LIST = [SERVICE_TYPE_AUTO_STR, SERVICE_TYPE_CAB_STR]
SERVICE_TYPE_CHOICES = [(choice, choice) for choice in SERVICE_TYPE_LIST]

PAYMENT_MODE_CASH = "cash"


class NammayatriCancellationReasons:
    ORDER_CANCELLED_BY_CUSTOMER = "Order cancelled by customer"
    FOUND_ANOTHER_MODE_OF_COMMUTE = "Found another mode of commute"
    ORDER_CANCELLED_BEFORE_RIDER_ACCEPTED = "Order Cancelled before rider accepted"
    ASKED_TO_CHANGE_PAYMENT_MODE = "Asked to change payment mode"
    ASKED_TO_PAY_EXTRA = "Asked to pay extra"
    DROP_LOCATION_DENIED = "Drop location denied"
    SAFETY_SEEMS_TO_BE_AN_ISSUE = "Safety seems to be an issue"
    RUDE_BEHAVIOR = "Rude behavior"
    TAKING_LONGER_THAN_EXPECTED = "Taking longer than expected"


class NammayatriRideState:
    RIDE_ASSIGNED = "accepted"
    RIDE_STARTED = "started"
    RIDE_ENDED = "dropped"


# # custom x-api-key for this webhook
# class XAPIKeyPermission(BasePermission):
#     """
#     Authentication class for x-api-key.
#     """
#
#     def has_permission(self, request, view):
#         api_key = request.headers.get("x-api-key")
#         if not api_key:
#             raise AuthenticationFailed("API key not found.")
#         elif api_key == RAPIDO_WEBHOOK_X_API_KEY:
#             return True
#         raise AuthenticationFailed("Invalid API key.")
