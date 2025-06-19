from rest_framework import viewsets
from rest_framework.response import Response
from django.core.cache import cache
from nammayatri.constants import NammayatriRideState
from ondc_buyer_backend.constants import CACHE_DELIMITER, CACHE_TIMEOUT, AutoRideState
from ondc_buyer_backend.tasks.buyer_status import buyer_status
from ondc_buyer_backend.utils.check_ttl import check_ttl
from ondc_buyer_backend.utils.retry_decorator import retry_on_429_and_ssl_error
import logging
from ondc_buyer_backend.utils.timestamp_converter import convert_to_unix_timestamp, calculate_distance
from tickets.models.ticket_setup import TicketUpdate, Ticket
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ONDCBuyerOnConfirmViewSet(viewsets.GenericViewSet):
    @retry_on_429_and_ssl_error(retries=5, backoff_factor=0.3)
    def buyer_on_confirm(self, request, *args, **kwargs):
        try:
            ttl_check_response = check_ttl(request, "confirm")
            if ttl_check_response is not None:
                return ttl_check_response

            on_confirm_data = request.data
            # buyer_status.apply_async(args=[on_confirm_data])
            if request.method != "POST":
                return Response({"error": "Method or action not allowed"}, status=405)

            transaction_id = on_confirm_data.get('context', {}).get('transaction_id')
            if not transaction_id:
                return Response({"error": "Missing transaction ID"}, status=400)
            on_confirm_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:on_confirm"
            cache.set(on_confirm_cache_key, on_confirm_data, timeout=CACHE_TIMEOUT)
            on_confirm_cached_data = cache.get(on_confirm_cache_key)
            logging.fatal(f"Request from BPP ID==========: {on_confirm_data['context']['bpp_id']}")
            logging.info(f"on_confirm_data==========:{on_confirm_data}")

            message_data = on_confirm_data.get('message', {})
            order_id = message_data.get('order', {}).get('id')
            stops = on_confirm_data['message']['order']['fulfillments'][0]['stops']
            ride_state = on_confirm_data['message']['order']['fulfillments'][0]['state']['descriptor']['code']
            rider_name = on_confirm_data['message']['order']['fulfillments'][0]['agent']['person']['name']
            rider_mobile = on_confirm_data['message']['order']['fulfillments'][0]['agent']['contact']['phone']
            vehicle_number = on_confirm_data['message']['order']['fulfillments'][0]['vehicle']['registration']
            pnr_to_ondc_transaction_id_key = f"{transaction_id}:{CACHE_DELIMITER}:pnr"
            ticket_pnr = cache.get(pnr_to_ondc_transaction_id_key)
            ticket_obj = Ticket.objects.get(pnr=ticket_pnr)

            ride_otp = None
            for stop in stops:
                if stop.get('authorization'):
                    ride_otp = stop['authorization'].get('token')
                    break

            if ride_state == AutoRideState.RIDE_ASSIGNED:
                ticket_obj.ride_otp = ride_otp
                ticket_update_details = {
                    "eta": 1,
                    "otp": ride_otp,
                    "status": NammayatriRideState.RIDE_ASSIGNED,
                    "orderId": order_id,
                    "captainDetails": {
                        "name": rider_name,
                        "mobile": rider_mobile,
                        "currentVehicle": {
                            "number": vehicle_number
                        }
                    }
                }
            elif ride_state == AutoRideState.RIDE_ENDED:
                try:
                    start_timestamp = stops[0]['time']['timestamp']
                    end_timestamp = stops[-1]['time']['timestamp']
                    travel_duration = convert_to_unix_timestamp(end_timestamp) - convert_to_unix_timestamp(start_timestamp)
                    drop_time = convert_to_unix_timestamp(end_timestamp)
                    start_gps = stops[0]['location']['gps']
                    end_gps = stops[-1]['location']['gps']
                    fare = on_confirm_data['message']['order']['items'][0]['price']['value']

                    start_lat, start_lon = map(float, start_gps.split(', '))
                    end_lat, end_lon = map(float, end_gps.split(', '))
                    distance_travelled = calculate_distance(start_lat, start_lon, end_lat, end_lon)

                    ticket_update_details = {
                        "amount": float(fare),
                        "status": NammayatriRideState.RIDE_ENDED,
                        "orderId": order_id,
                        "dropTime": drop_time,
                        "travelDuration": travel_duration,
                        "distanceTravelled": round(distance_travelled, 2)
                    }
                except (IndexError, KeyError, ValueError) as e:
                    logger.error(f"Error processing ride ended state: {e}")
                    return Response({"error": "Invalid data structure or value"}, status=400)
            else:
                ticket_update_details = {
                    "status": NammayatriRideState.RIDE_STARTED,
                    "orderId": order_id,
                    "captainDetails": {
                        "name": rider_name,
                        "mobile": rider_mobile,
                        "currentVehicle": {
                            "number": vehicle_number
                        }
                    }
                }

            logger.info(f"Ticket update details: {ticket_update_details}")

            if not ticket_pnr:
                logger.error("PNR not found in cache")
                return Response({"error": "PNR not found"}, status=404)

            try:
                TicketUpdate.objects.create(ticket=ticket_obj, trigger_signal=True, details=ticket_update_details)
                logger.info("Ticket update saved successfully")
            except Ticket.DoesNotExist:
                logger.error(f"Ticket with PNR {ticket_pnr} does not exist")
                return Response({"error": "Ticket not found"}, status=404)
            except Exception as e:
                logger.error(f"Error saving ticket update: {e}")
                return Response({"error": "Database error"}, status=500)

            return Response({'message': {"ack": {"status": "ACK"}}}, status=200)
        
        except Exception as e:
            logging.error("Error in buyer_on_confirm: %s", str(e))
            return Response({'message': {"ack": {"status": "NACK", "tags": str(e)}}}, status=500)
