import logging
import time

from rest_framework import viewsets
from rest_framework.response import Response
from django.core.cache import cache
from ondc_buyer_backend.constants import CACHE_DELIMITER, CACHE_TIMEOUT
from ondc_buyer_backend.tasks.buyer_confirm import buyer_confirm
from ondc_buyer_backend.utils.check_ttl import check_ttl
from ondc_buyer_backend.utils.retry_decorator import retry_on_429_and_ssl_error


class ONDCBuyerOnInitViewSet(viewsets.GenericViewSet):
    @retry_on_429_and_ssl_error(retries=5, backoff_factor=0.3)
    def buyer_on_init(self, request, *args, **kwargs):
        ttl_check_response = check_ttl(request, "init")
        if ttl_check_response is not None:
            return ttl_check_response
        try:
            if request.method != "POST":
                return Response({"error": "Method not allowed"}, status=405)

            transaction_id = request.data.get('context', {}).get('transaction_id')
            if not transaction_id:
                return Response({"error": "Missing transaction ID"}, status=400)
            on_init_data = request.data
            logging.fatal(f"Request from BPP ID==========: {on_init_data['context']['bpp_id']}")
            logging.info(f"inside buyer on_init================={on_init_data}")
            on_init_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:on_init"
            cache.set(on_init_cache_key, on_init_data, timeout=CACHE_TIMEOUT)
            buyer_confirm.apply_async(args=[on_init_data])

            return Response({'message': {"ack": {"status": "ACK"}}}, status=200)
        
        except Exception as e:
            return Response({'message': {"ack": {"status": "NACK", "tags": str(e)}}}, status=500)
