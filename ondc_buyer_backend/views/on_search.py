import os

from rest_framework import viewsets
from rest_framework.response import Response
from django.core.cache import cache
from ondc_buyer_backend.constants import CACHE_DELIMITER, CACHE_TIMEOUT
from ondc_buyer_backend.utils.retry_decorator import retry_on_429_and_ssl_error
from ondc_buyer_backend.tasks.buyer_select import buyer_select
import logging
from django.conf import settings
from django.core.exceptions import RequestDataTooBig


class ONDCBuyerOnSearchViewSet(viewsets.GenericViewSet):
    @retry_on_429_and_ssl_error(retries=5, backoff_factor=0.3)
    def buyer_on_search(self, request, *args, **kwargs):
        # Check Content-Length header
        content_length = request.headers.get('Content-Length', 0)
        max_upload_size = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)  # Default 10 MB

        if int(content_length) > max_upload_size:
            return Response({"error": "Request data too large"}, status=413)  # HTTP 413 Payload Too Large
        on_search_request_data = request.data
        bpp_id = on_search_request_data.get('context', {}).get('bpp_id')
        try:
            if "error" in on_search_request_data:
                return Response({"error": "Invalid data format"}, status=400)

            if 'context' in on_search_request_data:
                transaction_id = on_search_request_data.get('context', {}).get('transaction_id')
                if not transaction_id:
                    return Response({"error": "Missing transaction ID"}, status=400)
                ALLOWED_BPP = os.getenv('BPP_ID').split(',')
                if bpp_id not in ALLOWED_BPP:
                    logging.info(f"on_search_data============: {on_search_request_data}")
                    return Response({'message': {'ack': {'status': 'NACK', 'tags': 'BPP not allowed.'}}}, status=400)

                logging.fatal(f"Request from BPP ID==========: {on_search_request_data['context']['bpp_id']}")
                logging.info(f"on_search_request_data==========: {on_search_request_data}")
                cache_key = f"{transaction_id}:{bpp_id}:{CACHE_DELIMITER}:on_search"
                cache.set(cache_key, request.data, timeout=CACHE_TIMEOUT)

                # Extract relevant data from the request JSON
                provider = request.data.get('message', {}).get('catalog', {}).get('providers', [])[0]

                quotes = []
                for fulfillment in provider.get('fulfillments', []):
                    fulfillment_id = fulfillment.get('id')
                    for item in provider.get('items', []):
                        logging.info(f"Item==========: {item.get('fulfillment_ids')}")
                        price = item.get('price', {})
                        vehicle_variant = item.get('descriptor')
                        if item.get('fulfillment_ids')[0] == fulfillment_id:
                            logging.info(f"Price==========: {price}, fulfillment ID: {item.get('fulfillment_ids')}")
                            quotes.append({
                                "totalAmount": price.get('value', None),
                                "dynamicSurge": 0,
                                "perKM": None,
                                "perMin": None,
                                "serviceType": vehicle_variant,
                                "staticSurge": 0,
                                "eta": None
                            })
                        elif fulfillment_id == item.get('fulfillment_ids'):
                            quotes.append({
                                "totalAmount": price.get('value', None),
                                "dynamicSurge": 0,
                                "perKM": None,
                                "perMin": None,
                                "serviceType": vehicle_variant,
                                "staticSurge": 0,
                                "eta": None
                            })

                # Format JSON as specified
                formatted_json = {
                        "status": "success",
                        "message": "",
                        "data": {
                            "requestId": transaction_id,
                            "rideTime": None,
                            "timeUnit": None,
                            "rideDistance": None,
                            "distanceUnit": None,
                            "quotes": quotes
                        }
                }

                logging.info(f"Formatted JSON==========: {formatted_json}")

                # Save the formatted JSON into the cache
                estimate_cache_key = f"{transaction_id}:{bpp_id}:{CACHE_DELIMITER}:on_estimate"
                cache.set(estimate_cache_key, formatted_json, timeout=CACHE_TIMEOUT)

                return Response({'message': {'ack': {'status': 'ACK'}}}, status=200)

            else:
                return Response({'message': {'ack': {'status': 'NACK'}}}, status=400)

        except RequestDataTooBig:
            return Response({"error": "Request body exceeded maximum size"}, status=413)
