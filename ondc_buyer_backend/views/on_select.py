from datetime import datetime, timezone
from rest_framework import viewsets
from rest_framework.response import Response
from django.core.cache import cache

from ondc_buyer_backend.constants import CACHE_DELIMITER, CACHE_TIMEOUT
from ondc_buyer_backend.utils.retry_decorator import retry_on_429_and_ssl_error
import logging
from ondc_buyer_backend.tasks.buyer_init import buyer_init

from ondc_buyer_backend.utils.check_ttl import check_ttl


class ONDCBuyerOnSelectViewSet(viewsets.GenericViewSet):
    @retry_on_429_and_ssl_error(retries=5, backoff_factor=0.3)
    def buyer_on_select(self, request, *args, **kwargs):
        ttl_check_response = check_ttl(request, "select")
        if ttl_check_response is not None:
            return ttl_check_response
        try:
            if request.method != "POST":
                return Response({"error": "Method not allowed"}, status=405)
            transaction_id = request.data.get('context', {}).get('transaction_id')
            if not transaction_id:
                return Response({"error": "Missing transaction ID"}, status=400)
            on_select_data = request.data
            logging.fatal(f"Request from BPP ID==========: {on_select_data['context']['bpp_id']}")
            logging.info(f"On_select received=============={on_select_data}")
            fare = on_select_data.get('message', {}).get('order', {}).get('quote', []).get('price', {}).get('value', 0)

            encoded_polyline = None
            fulfillment = on_select_data['message']['order']['fulfillments'][0]

            for tag in fulfillment.get('tags', []):
                if tag['descriptor']['code'] == 'ROUTE_INFO':
                    for item in tag.get('list', []):
                        if item['descriptor']['code'] == 'ENCODED_POLYLINE':
                            encoded_polyline = item['value']
                            break
                    if encoded_polyline:
                        break

            polyline = {
                "encoded_polyline": encoded_polyline
            }

            logging.info(f"Estimate data======={polyline}")

            on_select_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:on_select"
            on_estimate_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:polyline"

            cache.set(on_estimate_cache_key, polyline, timeout=CACHE_TIMEOUT)

            cache.set(on_select_cache_key, on_select_data, timeout=CACHE_TIMEOUT)

            transaction_id = on_select_data['context']['transaction_id']
            txn_canceled_key = f"{transaction_id}:{CACHE_DELIMITER}:txn_canceled"
            if cache.get(txn_canceled_key):
                return Response({'message': {"ack": {"status": "NACK", "tags": "Ride already canceled"}}}, status=500)
            else:
                buyer_init.apply_async(args=[on_select_data])
                return Response({'message': {'ack': {'status': 'ACK'}}}, status=200)
        
        except Exception as e:
            return Response({'message': {"ack": {"status": "NACK", "tags": str(e)}}}, status=500)
