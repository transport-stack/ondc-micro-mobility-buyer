# Create your views here.
import logging

from django.core.cache import cache
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.decorators import X_API_KEY_PARAMETERS
from modules.views import CustomJSONRenderer, XAPIKeyPermission
from nammayatri.serializers import CancelRequestSerializer
from nammayatri.wrapper.cancel import CancelAPI
from ondc_buyer_backend.constants import CACHE_DELIMITER
from ondc_buyer_backend.tasks.buyer_cancel import buyer_cancel
from tickets.models import Ticket
from tickets.models.ticket_setup import TicketUpdate


class CancelView(APIView):
    serializer_class = CancelRequestSerializer
    renderer_classes = [CustomJSONRenderer]
    permission_classes = [
        XAPIKeyPermission,
        IsAuthenticated,
    ]

    @extend_schema(
        tags=["NammaYatri_API"],
        parameters=X_API_KEY_PARAMETERS,
        responses={
            200: OpenApiResponse(
                description="Successful request.", response=serializer_class
            )
        },
        request=serializer_class,
    )
    def post(self, request, format=None):
        serializer = CancelRequestSerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            order_id = data.get("orderId")  # This is nothing but transaction_id but for this endpoint only
            cancel_reason = data.get("cancelReason")

            on_confirm_cache_key = f"{order_id}:{CACHE_DELIMITER}:on_confirm"
            cached_on_confirm_data = cache.get(on_confirm_cache_key)

            buyer_cancel.apply_async(args=[cached_on_confirm_data, cancel_reason])

            pnr_to_ondc_transaction_id_key = f"{order_id}:{CACHE_DELIMITER}:pnr"
            ticket_pnr = cache.get(pnr_to_ondc_transaction_id_key)

            ticket_update_details = {
                      "status": "cancel_by_user",
                      "description": ""
                    }
            ticket_obj = Ticket.objects.get(pnr=ticket_pnr)
            ticket_update = TicketUpdate.objects.create(ticket=ticket_obj, trigger_signal=True, details=ticket_update_details)
            ticket_update.save()
            logging.info("Ticket update saved successfully")

            return Response("Cancellation initiated", status=200)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
