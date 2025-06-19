import logging
import os
import uuid
from time import sleep

from django.core.cache import cache
from rest_framework import viewsets
from rest_framework.response import Response

from modules.logger_main import logger
from ondc_buyer_backend.constants import CACHE_DELIMITER, CACHE_TIMEOUT
from ondc_buyer_backend.tasks.buyer_search import buyer_search

endpoint = "ptx_buyer_estimate"


class EstimateAPI(viewsets.ViewSet):

    def estimate_wrapper(self, route_id, start_stop_code, end_stop_code, variant, bus_reg_num, category="G", *args, **kwargs):

        try:
            print("inside buyer on estimate_wrapper=================", route_id, start_stop_code, end_stop_code, variant)  # For testing purposes only
            if not all([route_id, start_stop_code, end_stop_code]):
                return Response({"error": "Missing required fields"}, status=400)

            logger.debug(f"Dataaaaa================= {route_id}, {start_stop_code}, {end_stop_code}, {variant}, {bus_reg_num}")

            transaction_id = str(uuid.uuid4())
            route_id_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:route_id"
            cache.set(route_id_cache_key, route_id, timeout=CACHE_TIMEOUT)

            ticket_type = {
                "variant": variant,
                "category": category
            }

            variant_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:variant"
            cache.set(variant_cache_key, ticket_type, timeout=CACHE_TIMEOUT)
            BPP_ID = os.environ.get("BPP_ID")
            on_estimate_cache_key = f"{transaction_id}:{BPP_ID}:{CACHE_DELIMITER}:on_estimate"

            result = buyer_search(transaction_id, start_stop_code, end_stop_code, variant, bus_reg_num)
            logging.info("buyer_search_result::::::::::::::%s", result)

            logging.info("on_estimate cache data=================%s", cache.get(on_estimate_cache_key))
            estimate_data = None
            # Put a counter for only 10 iterations
            for i in range(10):
                estimate_data = cache.get(on_estimate_cache_key)
                if estimate_data is not None:
                    break
                sleep(1)

            return estimate_data
        except Exception as e:
            logging.error(f"Unexpected Error occurred: {e}")
            return False
