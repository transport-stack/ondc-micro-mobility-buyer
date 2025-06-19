from celery import shared_task
from datetime import datetime, timezone
import uuid
import logging
from django.core.cache import cache
from ondc_buyer_backend.constants import billing, init_settlement_data, location, CACHE_DELIMITER, TIMESTAMP_CACHE_TIMEOUT, CHARTR_GENERIC_USER_NAME
from ondc_buyer_backend.utils.post_request import post_request


@shared_task
def buyer_init(cached_on_select_data, *args, **kwargs):
    try:
        print("inside buyer init request.data=================", cached_on_select_data)
        # Deserialize the cached JSON data
        data = cached_on_select_data
        context = data['context']
        message = data['message']

        # Generate new message_id and timestamp
        new_message_id = str(uuid.uuid4())
        current_utc_datetime = datetime.now(timezone.utc)
        formatted_current_utc = current_utc_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        stops = message['order']['fulfillments'][0]['stops']
        vehicle = message['order']['fulfillments'][0]['vehicle']
        start_location = stops[0]['location']['gps']
        end_location = stops[1]['location']['gps']
        fulfillment_id = message['order']['fulfillments'][0]['id']
        customer_phone_number = cache.get(f"{context['transaction_id']}:{CACHE_DELIMITER}:user_phone_number")

        # Construct the new request JSON
        seller_init_payload = {
            "context": {
                "location": location,
                "domain": "ONDC:TRV10",
                "action": "init",
                "version": "2.0.0",
                "bap_id": context['bap_id'],
                "bap_uri": context['bap_uri'],
                "bpp_id": context['bpp_id'],
                "bpp_uri": context['bpp_uri'],
                "transaction_id": context['transaction_id'],
                "message_id": new_message_id,
                "timestamp": formatted_current_utc,
                "ttl": "PT30S"
            },
            "message": {
                "order": {
                    "items": [
                        {
                            "id": message['order']['items'][0]['id']
                        }
                    ],
                    "provider": {
                        "id": message['order']['provider']['id']
                    },
                    "fulfillments": [
                        {
                            "customer": {
                                "contact": {
                                    "phone": customer_phone_number
                                },
                                "person": {
                                    "name": CHARTR_GENERIC_USER_NAME
                                }
                            },
                            "id": fulfillment_id,
                            "stops": [
                                {
                                  "location": {
                                    "gps": start_location,
                                  },
                                  "type": "START"
                                },
                                {
                                  "location": {
                                    "gps": end_location,
                                  },
                                  "type": "END"
                                }
                              ],
                            "vehicle": vehicle,
                        }

                    ],
                    "billing": billing,
                    "payments": [
                        init_settlement_data
                    ]
                }
            }
        }

        logging.info(f"seller_init_payload================={seller_init_payload}")  # For testing purposes only
        bpp_url = context['bpp_uri']+'/init'
        post_result = post_request(bpp_url, seller_init_payload)

        init_start_time_cache_key = f"{context['transaction_id']}:{CACHE_DELIMITER}:init_start_time"

        cache.set(init_start_time_cache_key, formatted_current_utc, timeout=TIMESTAMP_CACHE_TIMEOUT)
        return post_result
    
    except Exception as e:
        logging.error(f"Error in buyer_init: {e}")
        return {'error': str(e)}
