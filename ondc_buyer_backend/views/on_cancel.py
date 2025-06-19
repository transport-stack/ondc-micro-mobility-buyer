import logging
from rest_framework import viewsets
from rest_framework.response import Response
from django.core.cache import cache
from ondc_buyer_backend.constants import CACHE_DELIMITER, CACHE_TIMEOUT
from ondc_buyer_backend.utils.check_ttl import check_ttl
from ondc_buyer_backend.utils.retry_decorator import retry_on_429_and_ssl_error
from tickets.models import Ticket
from tickets.models.ticket_setup import TicketUpdate


class ONDCBuyerOnCancelViewSet(viewsets.GenericViewSet):
    @retry_on_429_and_ssl_error(retries=5, backoff_factor=0.3)
    def buyer_on_cancel(self, request, *args, **kwargs):
        ttl_check_response = check_ttl(request, "cancel")
        if ttl_check_response is not None:
            return ttl_check_response
        try:
            on_cancel_data = request.data
            logging.fatal(f"Request from BPP ID==========: {on_cancel_data['context']['bpp_id']}")
            logging.info(f"inside buyer on cancel request.data================={on_cancel_data}")  # For testing purposes only
            if request.method != "POST":
                return Response({"error": "Method not allowed"}, status=405)

            transaction_id = request.data.get('context', {}).get('transaction_id')
            if not transaction_id:
                return Response({"error": "Missing transaction ID"}, status=400)

            order_id = on_cancel_data.get('message', {}).get('order', {}).get('id')

            on_cancel_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:on_cancel"
            cache.set(on_cancel_cache_key, request.data, timeout=CACHE_TIMEOUT)
            pnr_to_ondc_transaction_id_key = f"{transaction_id}:{CACHE_DELIMITER}:pnr"
            ticket_pnr = cache.get(pnr_to_ondc_transaction_id_key)

            ticket_update_details = {
                "status": "customer_cancelled",
                "orderId": order_id
            }
            ticket_obj = Ticket.objects.get(pnr=ticket_pnr)
            ticket_update = TicketUpdate.objects.create(ticket=ticket_obj, trigger_signal=True, details=ticket_update_details)
            ticket_update.save()
            logging.info("Ticket update saved successfully")

            return Response({'message': {"ack": {"status": "ACK"}}}, status=200)

        except Exception as e:
            return Response({'message': {"ack": {"status": "NACK", "tags": str(e)}}}, status=500)
