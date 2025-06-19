import json
import logging
from enum import Enum
from typing import Dict

from modules.pg.paytm.wrapper.base import PaytmAPIWrapper


class PayTMPaymentMode:
    """
    BALANCE, UPI , UPI_INTENT , CREDIT_CARD , DEBIT_CARD , NET_BANKING , EMI
    """

    BALANCE = "BALANCE"
    UPI = "UPI"
    UPI_INTENT = "UPI_INTENT"
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    NET_BANKING = "NET_BANKING"
    EMI = "EMI"


class ProcessTransaction(PaytmAPIWrapper):
    def __init__(self):
        super().__init__()

    def run(self, order_id: str, payment_mode: str, transaction_token: str, callback_url: None) -> Dict:
        """
        :param payment_mode:
        BALANCE (For Paytm Wallet)BALANCE, UPI , UPI_INTENT , CREDIT_CARD , DEBIT_CARD , NET_BANKING , EMI
        """
        # TODO: make payment mode generic for non UPI INTENT
        self.callback_url = callback_url

        paytm_body = {
            "head": {"txnToken": transaction_token},
            "body": {
                "requestType": "NATIVE",
                "mid": self.merchant_id,
                "orderId": order_id,
                "paymentMode": payment_mode,
                "authMode": "otp",
            },
        }

        suffix_url = "/theia/api/v1/processTransaction?mid={}&orderId={}".format(
            self.merchant_id, order_id
        )
        try:
            response = self.post_data(suffix_url, paytm_body, add_checksum=False)
            logging.debug("Response from Paytm: %s", json.dumps(response))
        except Exception as e:
            logging.error(
                "Couldn't connect to Paytm server in OrderProcess. Error: %s", e
            )
            raise
        self.response = response
        return response
