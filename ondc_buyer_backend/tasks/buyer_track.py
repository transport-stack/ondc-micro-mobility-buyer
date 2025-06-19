import logging
from datetime import datetime, timezone
import uuid
import json
from celery import shared_task
from django.core.cache import cache
from modules.logger_main import logger
from ondc_buyer_backend.constants import CACHE_DELIMITER, TIMESTAMP_CACHE_TIMEOUT, location
from ondc_buyer_backend.utils.post_request import post_request


@shared_task
def buyer_track(cached_on_confirm_data, **kwargs):
    try:
        on_confirm_data = json.loads(cached_on_confirm_data) if isinstance(cached_on_confirm_data, str) else cached_on_confirm_data

        context = on_confirm_data['context']
        message = on_confirm_data['message']
        current_utc_datetime = datetime.now(timezone.utc)
        formatted_current_utc = current_utc_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        order_id = message['order']['id']

        seller_track_payload = {
            "context": {
                "location": location,
                "domain": "ONDC:TRV10",
                "action": "track",
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
                "order_id": order_id
            }
        }
        logging.info(f"seller_track_payload============: {seller_track_payload}")

        SELLER_APP_SITE_URL = context['bpp_uri'] + '/track'
        post_result = post_request(SELLER_APP_SITE_URL, seller_track_payload)

        track_start_time_cache_key = f"{context['transaction_id']}:{CACHE_DELIMITER}:track_start_time"
        cache.set(track_start_time_cache_key, formatted_current_utc, timeout=TIMESTAMP_CACHE_TIMEOUT)

        return post_result

    except Exception as e:
        logger.error(f"Error in buyer_track: {e}")
        raise
