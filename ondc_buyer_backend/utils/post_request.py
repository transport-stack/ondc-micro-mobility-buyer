import json
import logging
import os
from datetime import datetime, timezone
import requests
from celery.utils.log import get_task_logger
from modules.ondc_signature_generator.cryptic_utils import create_authorisation_header, verify_authorisation_header

logger = get_task_logger(__name__)


def post_request(url, data, *args):
    try:
        current_utc_datetime = datetime.now(timezone.utc)
        formatted_current_utc = current_utc_datetime.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        request_body_raw_text = json.dumps(data, separators=(',', ':'))
        logging.info(f"Request body:================= {request_body_raw_text}")
        signature = create_authorisation_header(request_body=request_body_raw_text, created=None, expires=None)
        signature = signature[1:-1]
        logging.info(f"signature:================== {signature}")
        verified = verify_authorisation_header(f'{signature}', request_body_str=request_body_raw_text,
                                               public_key=os.environ.get("PUBLIC_KEY"))
        logging.info(f"verified:=================== {verified}")

        headers = {
            'Authorization': signature,
            'Content-Type': 'application/json',
            'X-Timestamp': formatted_current_utc
        }
        logging.info(f"Headers:==================== {headers}")
        logging.info(f"Posting request to url=========: {url}")
        post_result = requests.post(url, data=request_body_raw_text, headers=headers)
        post_result.raise_for_status()

        return post_result.json()

    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP error during select operation: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
