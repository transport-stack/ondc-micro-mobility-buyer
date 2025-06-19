import logging
from rest_framework import viewsets
from rest_framework.response import Response
from django.core.cache import cache
from nammayatri.constants import NammayatriRideState
from ondc_buyer_backend.constants import CACHE_DELIMITER, CACHE_TIMEOUT, AutoRideState
from ondc_buyer_backend.utils.check_ttl import check_ttl
from ondc_buyer_backend.utils.retry_decorator import retry_on_429_and_ssl_error
from tickets.models import Ticket
from tickets.models.ticket_setup import TicketUpdate

# Configure the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ONDCBuyerOnStatusViewSet(viewsets.GenericViewSet):
    @retry_on_429_and_ssl_error(retries=5, backoff_factor=0.3)
    def buyer_on_status(self, request, *args, **kwargs):
        # ttl_check_response = check_ttl(request, "status")
        # if ttl_check_response is not None:
        #     return ttl_check_response

        try:
            on_status_data = request.data
            logger.info(f"Received request from BPP ID: {on_status_data.get('context', {}).get('bpp_id', 'N/A')}")
            logger.debug(f"on_status Request data=======: {on_status_data}")  # For detailed logging

            if request.method != "POST":
                logger.warning("Request method not allowed")
                return Response({"error": "Method not allowed"}, status=405)

            transaction_id = on_status_data.get('context', {}).get('transaction_id')
            if not transaction_id:
                logger.warning("Missing transaction ID")
                return Response({"error": "Missing transaction ID"}, status=400)

            message_data = on_status_data.get('message', {})
            order_id = message_data.get('order', {}).get('id')
            if not order_id:
                logger.warning("Missing order ID")
                return Response({"error": "Missing order ID"}, status=400)

            on_status_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:on_status"
            cache.set(on_status_cache_key, on_status_data, timeout=CACHE_TIMEOUT)
            logger.info(f"Cached data for transaction ID {transaction_id}")

            pnr_to_ondc_transaction_id_key = f"{transaction_id}:{CACHE_DELIMITER}:pnr"
            ticket_pnr = cache.get(pnr_to_ondc_transaction_id_key)
            if not ticket_pnr:
                logger.error("PNR not found in cache")
                return Response({"error": "PNR not found"}, status=404)

            try:
                stops = on_status_data['message']['order']['fulfillments'][0]['stops']
                ride_state = on_status_data['message']['order']['fulfillments'][0]['state']['descriptor']['code']
                rider_name = on_status_data['message']['order']['fulfillments'][0]['agent']['person']['name']
                rider_mobile = on_status_data['message']['order']['fulfillments'][0]['agent']['contact']['phone']
                vehicle_number = on_status_data['message']['order']['fulfillments'][0]['vehicle']['registration']

                ride_otp = None
                for stop in stops:
                    if stop.get('authorization'):
                        ride_otp = stop['authorization'].get('token')
                        break

                ticket_update_details = {
                    "otp": ride_otp,
                    "status": NammayatriRideState.RIDE_STARTED if ride_state == AutoRideState.RIDE_STARTED else NammayatriRideState.RIDE_ASSIGNED,
                    "orderId": order_id,
                    "captainDetails": {
                        "name": rider_name,
                        "mobile": rider_mobile,
                        "currentVehicle": {
                            "number": vehicle_number
                        }
                    }
                }

                ticket_obj = Ticket.objects.get(pnr=ticket_pnr)
                ticket_update = TicketUpdate.objects.create(ticket=ticket_obj, trigger_signal=True, details=ticket_update_details)
                ticket_update.save()
                logger.info("Ticket update saved successfully")

            except (IndexError, KeyError) as e:
                logger.error(f"Error processing status data: {e}")
                return Response({"error": "Invalid data structure or value"}, status=400)
            except Ticket.DoesNotExist:
                logger.error(f"Ticket with PNR {ticket_pnr} does not exist")
                return Response({"error": "Ticket not found"}, status=404)
            except Exception as e:
                logger.error(f"Error saving ticket update: {e}")
                return Response({"error": "Database error"}, status=500)

            return Response({'message': {"ack": {"status": "ACK"}}}, status=200)

        except Exception as e:
            logger.error(f"Unexpected error in buyer_on_status: {e}")
            return Response({'message': {"ack": {"status": "NACK", "tags": str(e)}}}, status=500)
