import logging

from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.decorators import X_API_KEY_PARAMETERS
from modules.views import CustomJSONRenderer, XAPIKeyPermission
from nammayatri.serializers import (
    OrderUpdateSerializer,
    LocationUpdateSerializer,
)
from ondc_buyer_backend.constants import CACHE_DELIMITER
from tickets.models.ticket_setup import TicketUpdate, Ticket


class OrderUpdateView(APIView):
    serializer_class = OrderUpdateSerializer
    renderer_classes = [CustomJSONRenderer]
    permission_classes = [
        XAPIKeyPermission,
        IsAuthenticated,
    ]

    @extend_schema(tags=["NammaYatri_API"], parameters=X_API_KEY_PARAMETERS)
    def post(self, request, format=None):
        """
        # Cases
        Name
        Description

        Accepted
        Sent when an order is accepted by rider

        Arrived
        Sent when rider has arrived at the pickup location

        Started
        Sent when rider has started the ride

        Dropped
        Sent when rider has dropped the customer

        Aborted
        Sent when an order is aborted - incase of internal system failure orders are aborted or can be done via CCC call

        Expired
        Sent when an order is expired

        Customer Cancelled
        Sent when an order is cancelled by client (via API) or customer

        Rider cancelled
        Sent when an order is cancelled by rider
        """
        logging.info(f"OrderUpdateView: {request.data}")
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            response_data = serializer.validated_data
            transaction_id = response_data["transaction_id"]




            return Response({}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# class LocationUpdateView(APIView):
#     serializer_class = LocationUpdateSerializer
#     renderer_classes = [CustomJSONRenderer]
#     permission_classes = [
#         XAPIKeyPermission,
#         IsAuthenticated,
#     ]
#
#     @extend_schema(
#         tags=["NammaYatri_API"],
#         parameters=X_API_KEY_PARAMETERS,
#         examples=[
#             OpenApiExample(
#                 "Example 1",
#                 summary="Multiple location updates",
#                 description="Multiple location updates",
#                 value={
#                     "data": [
#                         {
#                             "status": "accepted",
#                             "location": {
#                                 "latitude": 12.917650810388636,
#                                 "longitude": 77.62248223786224,
#                             },
#                             "timestamp": 1618420912065,
#                             "order_id": "d7e96e61-2394-4c27-a295-cf496cd93224",
#                         },
#                         {
#                             "status": "arrived",
#                             "location": {
#                                 "latitude": 12.917401377481589,
#                                 "longitude": 77.6224747672677,
#                             },
#                             "timestamp": 1618420912065,
#                             "order_id": "d7e96e61-2394-4c27-a295-cf496cd93224",
#                         },
#                     ]
#                 },
#             )
#         ],
#     )
#     def post(self, request, format=None):
#         logging.info(f"LocationUpdateView: {request.data}")
#         # Handle multiple data entries
#         data = request.data["data"]
#         if not isinstance(data, list):
#             data = [data]
#
#         serializer = self.serializer_class(data=request.data["data"], many=True)
#         if serializer.is_valid(raise_exception=True):
#             ticket_updates_to_create = []  # list to store instances for bulk creation
#
#             for validated_data in serializer.validated_data:
#                 serialized_data = validated_data
#                 order_id = validated_data["order_id"]
#                 validated_data["status"] = ""
#
#                 if "timestamp_iso" in serialized_data:
#                     validated_data["timestamp_iso"] = serialized_data["timestamp_iso"]
#
#                 # compute ETA
#                 ticket_update = TicketUpdate.build_instance(
#                     details=validated_data,
#                     ticket_transit_pnr=order_id,
#                     trigger_signal=False,
#                 )
#
#                 if ticket_update:  # Only add to the list if the ticket was found
#                     ticket_updates_to_create.append(ticket_update)
#                 #
#                 # ticket_update = TicketUpdate.build_instance(
#                 #     details=validated_data,
#                 #     ticket_transit_pnr=order_id,
#                 #     trigger_signal=False,
#                 # )
#                 # ticket_updates_to_create.append(ticket_update)
#
#             # Bulk create all TicketUpdate instances at once
#             TicketUpdate.objects.bulk_create(ticket_updates_to_create)
#             return Response({}, status=status.HTTP_200_OK)
#
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
