import base64
import hashlib
import json

import requests

from modules.env_main import (
    PHONEPE_PG_BASE_URL,
    PHONEPE_PG_KEY_1,
    PHONEPE_PG_MERCHANT_ID,
)

PREPROD_ENV = "UAT"
PROD_ENV = "PROD"

PREPROD_URL = "https://mercury-uat.phonepe.com"
PROD_URL = "https://mercury.phonepe.com"

URLS = {PREPROD_ENV: PREPROD_URL, PROD_ENV: PROD_URL}

BASE_URL = PHONEPE_PG_BASE_URL
MERCHANT_ID = PHONEPE_PG_MERCHANT_ID
STORE_ID = "test_store"
TERMINAL_ID = "test_terminal"

API_KEYS = {1: PHONEPE_PG_KEY_1}

DEBIT_ENDPOINT = "/v4/debit"
QRINIT_ENDPOINT = "/v3/qr/init"
CHARGE_ENDPOINT = "/v3/charge"
TRANSACTION_ENDPOINT = "/v3/transaction"
REFUND_ENDPOINT = "/v3/credit/backToSource"


def set_environment(ENV):
    global BASE_URL
    BASE_URL = URLS[ENV]


def make_base64(json_obj):
    json_str = json.dumps(json_obj, separators=(",", ":"))  # compact encoding
    return base64.urlsafe_b64encode(bytes(json_str, "utf-8")).decode("utf-8")


def make_hash(input_str):
    m = hashlib.sha256()
    m.update(input_str.encode())
    return m.hexdigest()


def make_request_body(base64_payload):
    request_body = {"request": base64_payload}
    data_json = json.dumps(request_body)
    return data_json


def get_debit_request_params(
    amount, transaction_id, PHONEPE_ANDROID_CUSTOM_OPEN_INTENT_SDK=False
):
    _ENDPOINT_USED = DEBIT_ENDPOINT
    request_payload = {
        "merchantId": MERCHANT_ID,
        "transactionId": transaction_id,
        "amount": amount,
        "merchantUserId": transaction_id,
        "merchantOrderId": transaction_id,
    }

    if PHONEPE_ANDROID_CUSTOM_OPEN_INTENT_SDK:
        request_payload["paymentScope"] = "ALL_UPI_APPS"
        request_payload["openIntentWithApp"] = "GPay"

    salt_key_index = 1
    # encoded payload
    base64_payload = make_base64(request_payload)
    verification_str = base64_payload + _ENDPOINT_USED + API_KEYS[salt_key_index]

    # checksum
    checksum = "{}{}{}".format(make_hash(verification_str), "###", salt_key_index)

    return base64_payload, checksum, _ENDPOINT_USED


def make_charge_request(amount, transaction_id, mobile_number, salt_key_index):
    request_payload = {
        "amount": amount,  # Amount in paise
        "expiresIn": 180,
        "instrumentReference": mobile_number,
        "instrumentType": "MOBILE",
        "merchantOrderId": transaction_id,
        "storeId": STORE_ID,
        "terminalId": TERMINAL_ID,
        "transactionId": transaction_id,
        "message": "Payment for " + transaction_id,
    }

    # encoded payload
    base64_payload = make_base64(request_payload)
    verification_str = base64_payload + CHARGE_ENDPOINT + API_KEYS[salt_key_index]

    # checksum
    X_VERIFY = make_hash(verification_str) + "###" + salt_key_index

    url = BASE_URL + CHARGE_ENDPOINT
    data = make_request_body(base64_payload)
    headers = {"Content-Type": "application/json", "X-VERIFY": X_VERIFY}

    response = requests.request("POST", url, data=data, headers=headers)
    print(response.status_code, response.text)
    return response


def make_qrinit_request(amount, transaction_id, salt_key_index):
    request_payload = {
        "amount": amount,  # Amount in paise
        "expiresIn": 180,
        "merchantId": MERCHANT_ID,
        "merchantOrderId": transaction_id,
        "storeId": STORE_ID,
        "terminalId": TERMINAL_ID,
        "transactionId": transaction_id,
        "message": "Payment for " + transaction_id,
    }

    base64_payload = make_base64(request_payload)
    verification_str = base64_payload + QRINIT_ENDPOINT + API_KEYS[salt_key_index]
    X_VERIFY = make_hash(verification_str) + "###" + salt_key_index

    url = BASE_URL + QRINIT_ENDPOINT
    data = make_request_body(base64_payload)
    headers = {"Content-Type": "application/json", "X-VERIFY": X_VERIFY}

    response = requests.request("POST", url, data=data, headers=headers)
    print(response.status_code, response.text)
    return response


def make_status_request(transaction_id, salt_key_index):
    endpoint = (
        TRANSACTION_ENDPOINT + "/" + MERCHANT_ID + "/" + transaction_id + "/status"
    )
    verification_str = endpoint + API_KEYS[salt_key_index]
    X_VERIFY = make_hash(verification_str) + "###" + salt_key_index

    url = BASE_URL + endpoint
    headers = {"Content-Type": "application/json", "X-VERIFY": X_VERIFY}

    response = requests.request("GET", url, headers=headers)
    print(response.status_code, response.text)
    return response


def make_cancel_request(transaction_id, salt_key_index):
    endpoint = CHARGE_ENDPOINT + "/" + MERCHANT_ID + "/" + transaction_id + "/cancel"
    verification_str = endpoint + API_KEYS[salt_key_index]
    X_VERIFY = make_hash(verification_str) + "###" + salt_key_index

    url = BASE_URL + endpoint
    headers = {"Content-Type": "application/json", "X-VERIFY": X_VERIFY}

    response = requests.request("POST", url, headers=headers)
    print(response.status_code, response.text)
    return response


def make_refund_request(transaction_id, provider_reference_id, amount, salt_key_index):
    assert amount is not None

    request_payload = {
        "amount": amount,
        "merchantId": MERCHANT_ID,
        "providerReferenceId": provider_reference_id,
        "transactionId": transaction_id + "_refund",
        "message": "Refund",
    }

    base64_payload = make_base64(request_payload)
    verification_str = base64_payload + REFUND_ENDPOINT + API_KEYS[salt_key_index]
    X_VERIFY = "{}{}{}".format(make_hash(verification_str), "###", salt_key_index)

    url = BASE_URL + REFUND_ENDPOINT
    data = make_request_body(base64_payload)
    headers = {"Content-Type": "application/json", "X-VERIFY": X_VERIFY}

    response = requests.request("POST", url, data=data, headers=headers)
    print(response.status_code, response.text)
    return response
