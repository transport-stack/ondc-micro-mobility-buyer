from rest_framework import viewsets
from rest_framework.response import Response
from django.core.cache import cache
from nammayatri.constants import NammayatriRideState
from ondc_buyer_backend.constants import CACHE_DELIMITER, CACHE_TIMEOUT, AutoRideState, AutoRideStatus
import logging
from ondc_buyer_backend.utils.timestamp_converter import convert_to_unix_timestamp, calculate_distance
from tickets.models.fare_setup import FareBreakup
from tickets.models.ticket_setup import TicketUpdate, Ticket

# Configure the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ONDCBuyerOnUpdateViewSet(viewsets.GenericViewSet):
    def buyer_on_update(self, request, *args, **kwargs):
        try:
            on_update_data = request.data
            logger.info(f"Received request from BPP ID: {on_update_data.get('context', {}).get('bpp_id', 'N/A')}")
            logger.debug(f"on_update Request data===========: {on_update_data}")

            if request.method != "POST":
                logger.warning("Request method not allowed")
                return Response({"error": "Method not allowed"}, status=405)

            transaction_id = on_update_data.get('context', {}).get('transaction_id')
            if not transaction_id:
                logger.warning("Missing transaction ID")
                return Response({"error": "Missing transaction ID"}, status=400)

            message_data = on_update_data.get('message', {})
            order_id = message_data.get('order', {}).get('id')
            if not order_id:
                logger.warning("Missing order ID")
                return Response({"error": "Missing order ID"}, status=400)

            on_update_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:on_update"
            cache.set(on_update_cache_key, on_update_data, timeout=CACHE_TIMEOUT)
            cached_data = cache.get(on_update_cache_key)
            logger.info(f"Cached data for transaction ID {transaction_id}")

            stops = on_update_data['message']['order']['fulfillments'][0]['stops']
            ride_state = on_update_data['message']['order']['fulfillments'][0]['state']['descriptor']['code']
            rider_name = on_update_data['message']['order']['fulfillments'][0]['agent']['person']['name']
            rider_mobile = on_update_data['message']['order']['fulfillments'][0]['agent']['contact']['phone']
            vehicle_number = on_update_data['message']['order']['fulfillments'][0]['vehicle']['registration']
            final_state = on_update_data['message']['order']['status']
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
            elif ride_state == AutoRideState.RIDE_ENDED and final_state == AutoRideStatus.COMPLETE:
                try:
                    start_timestamp = stops[0]['time']['timestamp']
                    end_timestamp = stops[-1]['time']['timestamp']
                    travel_duration = convert_to_unix_timestamp(end_timestamp) - convert_to_unix_timestamp(start_timestamp)
                    drop_time = convert_to_unix_timestamp(end_timestamp)
                    start_gps = stops[0]['location']['gps']
                    end_gps = stops[-1]['location']['gps']
                    fare = float(on_update_data['message']['order']['quote']['price']['value'])

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

                    fare_breakup_object = FareBreakup.objects.get(ticket=ticket_obj)
                    logger.info(f"Fare breakup object: {fare_breakup_object.basic}======={fare_breakup_object.amount}========={fare}")
                    fare_breakup_object.basic = fare
                    fare_breakup_object.amount = fare
                    fare_breakup_object.save()
                    logger.info(f"Fare breakup saved: {fare_breakup_object.basic}======={fare_breakup_object.amount}========={fare}")
                except (IndexError, KeyError, ValueError) as e:
                    logger.error(f"Error processing ride ended state: {e}")
                    return Response({"error": "Invalid data structure or value"}, status=400)

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
            logger.error(f"Unexpected error in buyer_on_update: {e}")
            return Response({'message': {"ack": {"status": "NACK", "tags": str(e)}}}, status=500)
