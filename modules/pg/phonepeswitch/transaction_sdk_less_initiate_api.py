import json

import requests

from modules.encoders_encrypters import *
from modules.pg.phonepeswitch.common import *
from modules.time_helpers import get_current_time_in_milli

base_url = PHONEPE_BASE_URL
url_suffix = PHONEPE_TRANSACTION_INITIATE_URL_SUFFIX
final_url = "{}{}".format(base_url, url_suffix)
# custom_print("final url", final_url)


def make_request_body(base64_payload):
    request_body = {"request": base64_payload}
    data_json = json.dumps(request_body)
    return data_json


def make_transaction_context_plain(
    transaction_amount, transaction_id=None, tracking_url=None
):
    transaction_context_payload_plain = {
        "orderContext": {
            "trackingInfo": {"type": "HTTPS", "url": "https://google.com"}
        },
        "fareDetails": {
            "totalAmount": transaction_amount,
            "payableAmount": transaction_amount,
        },
        "cartDetails": {
            "cartItems": [
                {
                    "category": "BUS",
                    "itemId": transaction_id,
                    "price": transaction_amount,
                    "itemName": "TICKET",
                    "quantity": 1,
                }
            ]
        },
    }
    return transaction_context_payload_plain


# update later:
# "redirectUrl": "https://chartr-app-c0d94.web.app/confirmation?
# booking_id=B08072021743cf3af3a&bus_name=DL1PC5335&fare=5.00"
def make_initiate_request(amount, transaction_id, redirect_url="/redirect-url"):
    _make_transaction_context_plain = make_transaction_context_plain(
        transaction_amount=amount, transaction_id=transaction_id
    )

    request_payload = {
        "merchantId": PHONEPE_MERCHANT_ID,
        "amount": amount,
        "validFor": VALIDITY_TIME_IN_MILLI,
        "transactionId": transaction_id,
        "merchantOrderId": transaction_id,
        "redirectUrl": redirect_url,
        "transactionContext": _make_transaction_context_plain,
    }

    # amount in paise
    base64_payload = base64_encode(json.dumps(request_payload))
    X_VERIFY = create_x_verify_hash(base64_payload, url_suffix)
    custom_print("base64_payload", base64_payload)
    custom_print("X_VERIFY", X_VERIFY)

    data = make_request_body(base64_payload)
    headers = {"Content-Type": "application/json", "X-VERIFY": X_VERIFY}

    url = final_url
    response = requests.request("POST", url, headers=headers, data=data)
    custom_print("response.status_code", response.status_code)
    custom_print("response.json()", response.json())
    return response, request_payload


if __name__ == "__main__":
    timestamp_in_milli = get_current_time_in_milli()
    custom_print("timestamp_in_milli", timestamp_in_milli)

    # transaction amount (paise)
    transaction_amount = 100
    make_initiate_request(amount=transaction_amount, transaction_id=timestamp_in_milli)
