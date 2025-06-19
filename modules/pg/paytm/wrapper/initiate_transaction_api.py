import json
import logging
from enum import Enum
from typing import Optional, Tuple

from modules.pg.paytm.wrapper.base import PaytmAPIWrapper


class ResultCode(Enum):
    SUCCESS = "0000"
    SUCCESS_IDEMPOTENT = "0002"
    PAYMENT_FAILED = "196"
    SESSION_EXPIRED = "1006"
    MISSING_ELEMENT = "1007"
    PIPE_NOT_ALLOWED = "1008"
    INVALID_PROMO = "1011"
    PROMO_AMOUNT_TOO_HIGH = "1012"
    INVALID_SSO_TOKEN = "2004"
    INVALID_CHECKSUM = "2005"
    INVALID_TXN_AMOUNT = "2007"
    MISMATCHED_MID = "2013"
    MISMATCHED_ORDER_ID = "2014"
    REPEAT_REQUEST_INCONSISTENT = "2023"
    SYSTEM_ERROR = "00000900"

    response_dict = {
        SUCCESS: {"resultCode": SUCCESS, "resultStatus": "S", "resultMsg": "Success"},
        SUCCESS_IDEMPOTENT: {
            "resultCode": SUCCESS_IDEMPOTENT,
            "resultStatus": "S",
            "resultMsg": "Success Idempotent",
        },
        PAYMENT_FAILED: {
            "resultCode": PAYMENT_FAILED,
            "resultStatus": "F",
            "resultMsg": "Payment failed as amount entered exceeds the allowed limit. Please enter a "
                         "lower amount and try again or reach out to the merchant for further assistance.",
        },
        SESSION_EXPIRED: {
            "resultCode": SESSION_EXPIRED,
            "resultStatus": "F",
            "resultMsg": "Your Session has expired",
        },
        MISSING_ELEMENT: {
            "resultCode": MISSING_ELEMENT,
            "resultStatus": "F",
            "resultMsg": "Missing mandatory element",
        },
        PIPE_NOT_ALLOWED: {
            "resultCode": PIPE_NOT_ALLOWED,
            "resultStatus": "F",
            "resultMsg": "Pipe character is not allowed",
        },
        INVALID_PROMO: {
            "resultCode": INVALID_PROMO,
            "resultStatus": "F",
            "resultMsg": "Invalid Promo Param",
        },
        PROMO_AMOUNT_TOO_HIGH: {
            "resultCode": PROMO_AMOUNT_TOO_HIGH,
            "resultStatus": "F",
            "resultMsg": "Promo amount cannot be more than transaction amount",
        },
        INVALID_SSO_TOKEN: {
            "resultCode": INVALID_SSO_TOKEN,
            "resultStatus": "F",
            "resultMsg": "SSO Token is invalid",
        },
        INVALID_CHECKSUM: {
            "resultCode": INVALID_CHECKSUM,
            "resultStatus": "F",
            "resultMsg": "Checksum provided is invalid",
        },
        INVALID_TXN_AMOUNT: {
            "resultCode": INVALID_TXN_AMOUNT,
            "resultStatus": "F",
            "resultMsg": "Txn amount is invalid",
        },
        MISMATCHED_MID: {
            "resultCode": MISMATCHED_MID,
            "resultStatus": "F",
            "resultMsg": "Mid in the query param doesn’t match with the Mid sent in the request",
        },
        MISMATCHED_ORDER_ID: {
            "resultCode": MISMATCHED_ORDER_ID,
            "resultStatus": "F",
            "resultMsg": "OrderId in the query param doesn’t match with the OrderId sent in the "
                         "request",
        },
        REPEAT_REQUEST_INCONSISTENT: {
            "resultCode": REPEAT_REQUEST_INCONSISTENT,
            "resultStatus": "F",
            "resultMsg": "Repeat Request Inconsistent",
        },
        SYSTEM_ERROR: {
            "resultCode": SYSTEM_ERROR,
            "resultStatus": "U",
            "resultMsg": "System error",
        },
    }


class InitiateTransaction(PaytmAPIWrapper):
    def __init__(self):
        super().__init__()

    def run(
            self,
            order_id: str,
            value: float,
            customer_id: Optional[str] = None,
            disabled_options: Optional[str] = None,
            callback_url: Optional[str] = None,
    ) -> Tuple[dict, dict]:
        if callback_url:
            self.callback_url = callback_url
        else:
            self.callback_url = f"{self.base_url}/theia/paytmCallback?ORDER_ID={order_id}"

        if not customer_id:
            customer_id = order_id

        paytm_body = {
            "requestType": "Payment",
            "mid": self.merchant_id,
            "websiteName": self.website_name,
            "orderId": order_id,
            "callbackUrl": self.callback_url,
            "txnAmount": {
                "value": value,
                "currency": "INR",
            },
            "userInfo": {
                "custId": customer_id,
            },
        }

        if disabled_options == "all":
            logging.debug(
                "disabled_options: %s, disabling non UPI options in Generation Transaction",
                disabled_options,
            )
            paytm_body["disablePaymentMode"] = [
                {"mode": "NET_BANKING"},
                {"mode": "CREDIT_CARD"},
                {"mode": "DEBIT_CARD"},
                {"mode": "BALANCE"},
            ]

        try:
            response = self.post_data(
                f"/theia/api/v1/initiateTransaction?mid={self.merchant_id}&orderId={order_id}",
                {"body": paytm_body},
                add_checksum=True,
            )
            self.transaction_token = response["body"]["txnToken"]
        except Exception as e:
            logging.error(
                "Couldn't connect to Paytm server in initiate_transaction. Error: %s", e
            )
            raise

        self.response = response
        return response
