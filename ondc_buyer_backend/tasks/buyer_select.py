from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, timezone
import uuid
import requests
import logging
from django.core.cache import cache
from ondc_buyer_backend.constants import CACHE_DELIMITER, TIMESTAMP_CACHE_TIMEOUT, PASSENGER_COUNT, location
from ondc_buyer_backend.utils.post_request import post_request

logger = get_task_logger(__name__)


@shared_task(bind=True, max_retries=3, retry_backoff=True, retry_backoff_max=30, retry_jitter=True)
def buyer_select(self, cached_on_search_data, vehicle, *args, **kwargs):
    try:
        data = cached_on_search_data
        transaction_id = data['context']['transaction_id']
        final_item_id = None
        final_provider_id = None
        final_fulfillment_id = None
        current_utc_datetime = datetime.now(timezone.utc)
        formatted_current_utc = current_utc_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        search_payload_key = f"{transaction_id}:{CACHE_DELIMITER}:search"
        cached_search_data = cache.get(search_payload_key)
        stops_data = cached_search_data['message']['intent']['fulfillment']['stops']
        start_location = stops_data[0]['location']['gps']
        end_location = stops_data[-1]['location']['gps']
        start_address = stops_data[0]['location']['address']
        end_address = stops_data[-1]['location']['address']
        tags_data = cached_search_data['message']['intent']['fulfillment']['tags']

        provider = data['message']['catalog']['providers'][0]

        # Create a dictionary mapping fulfillment IDs to fulfillment objects for quick lookup
        fulfillment_dict = {fulfillment['id']: fulfillment for fulfillment in provider['fulfillments']}

        # Iterate through each item in the provider's items and check fulfillments
        for item in provider['items']:
            for fulfillment_id in item.get('fulfillment_ids', []):
                fulfillment = fulfillment_dict.get(fulfillment_id)
                if fulfillment and fulfillment['vehicle']['category'] == vehicle:
                    final_item_id = item['id']
                    final_provider_id = provider['id']
                    final_fulfillment_id = fulfillment['id']
                    logger.info(
                        f"Match found: Provider ID={final_provider_id}, Item ID={final_item_id}, Fulfillment ID={final_fulfillment_id}"
                    )
                    break  # Break the loop if a match is found
            if final_fulfillment_id:
                break  # Break the outer loop if a match is found

        # Validate final selection
        if not final_fulfillment_id:
            logger.error("No matching fulfillment found for provided Vehicle")
            return {'error': 'No matching fulfillment found for provided Vehicle'}

        # Prepare payload for seller select action with the matching item_id
        seller_select_payload = {
            "context": {
                "location": location,
                "domain": "ONDC:TRV10",
                "action": "select",
                "version": "2.0.0",
                "bap_id": data['context']['bap_id'],
                "bap_uri": data['context']['bap_uri'],
                "bpp_id": data['context']['bpp_id'],
                "bpp_uri": data['context']['bpp_uri'],
                "transaction_id": transaction_id,
                "message_id": str(uuid.uuid4()),
                "timestamp": formatted_current_utc,
                "ttl": "PT30S"
            },
            "message": {
                "order": {
                    "items": [
                        {
                            "id": final_item_id,
                        }
                    ],
                    "provider": {
                        "id": final_provider_id
                    },
                    "fulfillments": [
                        {
                            "id": final_fulfillment_id,
                            "stops": [
                                {
                                  "location": {
                                    "gps": start_location,
                                    "address": start_address
                                  },
                                  "type": "START"
                                },
                                {
                                  "location": {
                                    "gps": end_location,
                                    "address": end_address
                                  },
                                  "type": "END"
                                }
                              ],
                            "vehicle": {
                                "category": vehicle,
                            },
                            "tags": tags_data

                        }
                    ]
                }
            }
        }
        logging.info(f"Sending seller select payload: {seller_select_payload}")

        bpp_url = data['context']['bpp_uri'] + '/select'
        post_result = post_request(bpp_url, seller_select_payload)

        select_start_time_cache_key = f"{transaction_id}:{CACHE_DELIMITER}:select_start_time"

        cache.set(select_start_time_cache_key, formatted_current_utc, timeout=TIMESTAMP_CACHE_TIMEOUT)
        select_timestamp_data = cache.get(select_start_time_cache_key)
        logging.info(f"select_timestamp_data==========: {select_timestamp_data}")
        return post_result

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error during select operation: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        self.retry(exc=e)
