import logging
from datetime import datetime, timezone
import uuid
import json
from celery import shared_task
from django.core.cache import cache
from modules.logger_main import logger
from ondc_buyer_backend.constants import billing, CACHE_DELIMITER, TIMESTAMP_CACHE_TIMEOUT, location, confirm_settlement_data
from ondc_buyer_backend.utils.post_request import post_request


@shared_task
def buyer_confirm(cached_on_init_data, *args, **kwargs):
    try:
        on_init_data = json.loads(cached_on_init_data) if isinstance(cached_on_init_data, str) else cached_on_init_data

        context = on_init_data['context']
        message = on_init_data['message']
        current_utc_datetime = datetime.now(timezone.utc)
        formatted_current_utc = current_utc_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        stops = message['order']['fulfillments'][0]['stops']
        vehicle = message['order']['fulfillments'][0]['vehicle']
        start_area = stops[0]['location']['address']
        end_area = stops[1]['location']['address']
        fulfillment_id = message['order']['fulfillments'][0]['id']
        customer_phone_number = message['order']['fulfillments'][0]['customer']['contact']['phone']
        customer_name = message['order']['fulfillments'][0]['customer']['person']['name']
        settlement_amount = message['order']['quote']['price']['value']

        seller_confirm_payload = {
            "context": {
                "location": location,
                "domain": "ONDC:TRV10",
                "action": "confirm",
                "version": "2.0.0",
                "bap_id": context['bap_id'],
                "bap_uri": context['bap_uri'],
                "bpp_id": context['bpp_id'],
                "bpp_uri": context['bpp_uri'],
                "transaction_id": context['transaction_id'],
                "message_id": str(uuid.uuid4()),
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
                                    "name": customer_name
                                }
                            },
                            "id": fulfillment_id,
                            "stops": stops,
                            "vehicle": vehicle,
                        }

                    ],
                    "billing": billing,
                    "payments": [
                        {
                            "collected_by": "BPP",
                            "id": "PA1",
                            "params": {
                                "bank_account_number": "xxxxxxxxxxxxxx",
                                "bank_code": "XXXXXXXX",
                            },
                            "status": "NOT-PAID",
                            "tags": [
                                {
                                    "descriptor": {
                                        "code": "BUYER_FINDER_FEES"
                                    },
                                    "display": False,
                                    "list": [
                                        {
                                            "descriptor": {
                                                "code": "BUYER_FINDER_FEES_PERCENTAGE"
                                            },
                                            "value": "0"
                                        }
                                    ]
                                },
                                {
                                    "descriptor": {
                                        "code": "SETTLEMENT_TERMS"
                                    },
                                    "display": False,
                                    "list": [
                                        {
                                            "descriptor": {
                                                "code": "SETTLEMENT_WINDOW"
                                            },
                                            "value": "PT60M"
                                        },
                                        {
                                            "descriptor": {
                                                "code": "SETTLEMENT_BASIS"
                                            },
                                            "value": "DELIVERY"
                                        },
                                        {
                                            "descriptor": {
                                                "code": "SETTLEMENT_TYPE"
                                            },
                                            "value": "UPI"
                                        },
                                        {
                                            "descriptor": {
                                                "code": "MANDATORY_ARBITRATION"
                                            },
                                            "value": "true"
                                        },
                                        {
                                            "descriptor": {
                                                "code": "COURT_JURISDICTION"
                                            },
                                            "value": "New Delhi"
                                        },
                                        {
                                            "descriptor": {
                                                "code": "DELAY_INTEREST"
                                            },
                                            "value": "0"
                                        },
                                        {
                                            "descriptor": {
                                                "code": "STATIC_TERMS"
                                            },
                                            "value": "https://example-test-bpp.com/static-terms.txt"
                                        },
                                        {
                                            "descriptor": {
                                                "code": "SETTLEMENT_AMOUNT"
                                            },
                                            "value": settlement_amount
                                        }
                                    ]
                                }
                            ],
                            "type": "ON-FULFILLMENT"
                        }
                    ]
                }
            }
        }
        logging.info(f"seller_confirm_payload============: {seller_confirm_payload}")

        SELLER_APP_SITE_URL = context['bpp_uri'] + '/confirm'
        post_result = post_request(SELLER_APP_SITE_URL, seller_confirm_payload)

        confirm_start_time_cache_key = f"{context['transaction_id']}:{CACHE_DELIMITER}:confirm_start_time"

        cache.set(confirm_start_time_cache_key, formatted_current_utc, timeout=TIMESTAMP_CACHE_TIMEOUT)
        confirm_timestamp_data = cache.get(confirm_start_time_cache_key)
        logging.info(f"confirm_timestamp_data==========: {confirm_timestamp_data}")
        return post_result

    except Exception as e:
        logger.error(f"Error in buyer_confirm: {e}")
        raise
