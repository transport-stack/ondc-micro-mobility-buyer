import logging
from rest_framework import viewsets
from rest_framework.response import Response
from django.core.cache import cache
from ondc_buyer_backend.constants import CACHE_DELIMITER, CACHE_TIMEOUT
from ondc_buyer_backend.utils.check_ttl import check_ttl
from ondc_buyer_backend.utils.retry_decorator import retry_on_429_and_ssl_error
from ondc_buyer_backend.utils.timestamp_converter import convert_to_unix_timestamp
from tickets.models import Ticket
from tickets.models.ticket_setup import TicketUpdate

# Configure the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class ONDCBuyerOnTrackViewSet(viewsets.GenericViewSet):
    def extract_lat_long(self, gps_string):
        # Split the GPS string into latitude and longitude
        lat, long = map(float, gps_string.split(", "))
        return lat, long
    @retry_on_429_and_ssl_error(retries=5, backoff_factor=0.3)
    def buyer_on_track(self, request, *args, **kwargs):
        ttl_check_response = check_ttl(request, "track")
        if ttl_check_response is not None:
            return ttl_check_response

        try:
            on_track_data = request.data
            logger.info(f"Received request from BPP ID: {on_track_data.get('context', {}).get('bpp_id', 'N/A')}")
            logger.debug(f"on_track Request data===========: {on_track_data}")  # For testing purposes only

            if request.method != "POST":
                logger.warning("Request method not allowed")
                return Response({"error": "Method not allowed"}, status=405)

            transaction_id = on_track_data.get('context', {}).get('transaction_id')
            if not transaction_id:
                logger.warning("Missing transaction ID")
                return Response({"error": "Missing transaction ID"}, status=400)

            on_track_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:on_track"
            cache.set(on_track_cache_key, on_track_data, timeout=CACHE_TIMEOUT)
            logger.info(f"Cached data for transaction ID {transaction_id}")
            ride_status = on_track_data['message']['tracking']['status']
            gps_data = on_track_data['message']['tracking']['location']['gps']
            latitude, longitude = self.extract_lat_long(gps_data)
            timestamp = on_track_data['message']['tracking']['location']['updated_at']

            on_confirm_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:on_confirm"
            cached_update_data = cache.get(on_confirm_cache_key)
            message_data = cached_update_data.get('message', {})
            order_id = message_data.get('order', {}).get('id')
            if not order_id:
                logger.warning("Missing order ID")
                return Response({"error": "Missing order ID"}, status=400)

            ticket_update_details = {
                              "status": ride_status,
                              "location": {
                                "latitude": latitude,
                                "longitude": longitude
                              },
                              "order_id": order_id,
                              "timestamp": convert_to_unix_timestamp(timestamp)
                            }

            pnr_to_ondc_transaction_id_key = f"{transaction_id}:{CACHE_DELIMITER}:pnr"
            ride_pnr = cache.get(pnr_to_ondc_transaction_id_key)
            if not ride_pnr:
                logger.error("PNR not found in cache")
                return Response({"error": "PNR not found"}, status=404)

            try:
                ticket_obj = Ticket.objects.get(pnr=ride_pnr)
                ticket_update = TicketUpdate.objects.create(ticket=ticket_obj, trigger_signal=False, details=ticket_update_details)
                ticket_update.save()
                logger.info("Ticket update saved successfully")
            except Ticket.DoesNotExist:
                logger.error(f"Ticket with PNR {ride_pnr} does not exist")
                return Response({"error": "Ticket not found"}, status=404)
            except Exception as e:
                logger.error(f"Error saving ticket update: {e}")
                return Response({"error": "Database error"}, status=500)

            return Response({'message': {"ack": {"status": "ACK"}}}, status=200)

        except Exception as e:
            logger.error(f"Unexpected error in buyer_on_track: {e}")
            return Response({'message': {"ack": {"status": "NACK", "tags": str(e)}}}, status=500)
