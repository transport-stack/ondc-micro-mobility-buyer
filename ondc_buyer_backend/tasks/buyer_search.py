import uuid
import os
import logging
from celery import shared_task
from datetime import datetime, timezone
from ondc_buyer_backend.constants import location, search_payload_payments_obj
from django.core.cache import cache
from ondc_buyer_backend.constants import TIMESTAMP_CACHE_TIMEOUT, CACHE_DELIMITER
from ondc_buyer_backend.utils.post_request import post_request


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=30, retry_jitter=True)
def buyer_search(self, transaction_id, formatted_pickup_location, pickupAddress, formatted_drop_location, dropAddress, *args, **kwargs):
    try:
        current_utc_datetime = datetime.now(timezone.utc)
        formatted_current_utc = current_utc_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        seller_search_payload = {
            "context": {
                "location": location,
                "domain": "ONDC:TRV10",
                "timestamp": formatted_current_utc,
                "bap_id": os.environ.get("BAP_ID"),
                "transaction_id": transaction_id, 
                "message_id": str(uuid.uuid4()),
                "version": "2.0.0",
                "action": "search",
                "bap_uri": os.environ.get("BAP_URI"),
                "ttl": "PT30S"
            },
            "message": {
                "intent": {
                    "fulfillment": {
                        "stops": [
                          {
                            "location": {
                              "gps": formatted_pickup_location,
                              "address": pickupAddress
                            },
                            "type": "START"
                          },
                          {
                            "location": {
                              "gps": formatted_drop_location,
                              "address": dropAddress
                            },
                            "type": "END"
                          }
                        ],
                        "tags": [
                            {
                                "descriptor": {
                                    "code": "LOCATION"
                                },
                                "display": False,
                                "list": [
                                    {
                                        "descriptor": {
                                            "code": "START_AREA"
                                        },
                                        "value": pickupAddress
                                    },
                                    {
                                        "descriptor": {
                                            "code": "END_AREA"
                                        },
                                        "value": dropAddress
                                    }
                                ]
                            }
                        ]
                    },
                    "payment": search_payload_payments_obj
                }
            }
        }
        logging.info(f"seller_search_payload:================== {seller_search_payload}")

        search_payload_key = f"{transaction_id}:{CACHE_DELIMITER}:search"
        cache.set(search_payload_key, seller_search_payload, timeout=TIMESTAMP_CACHE_TIMEOUT)
        ONDC_SEARCH_URL = os.environ.get("ONDC_SEARCH_URL")
        post_result = post_request(ONDC_SEARCH_URL, seller_search_payload)

        search_start_time_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:search_start_time"

        cache.set(search_start_time_cache_key, formatted_current_utc, timeout=TIMESTAMP_CACHE_TIMEOUT)
        search_timestamp_data = cache.get(search_start_time_cache_key)
        logging.info(f"search_timestamp_data==========: {search_timestamp_data}")
        return post_result
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        self.retry(exc=e)
