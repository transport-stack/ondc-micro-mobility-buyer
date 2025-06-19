import json
import logging
import os

import requests

# .env.paytm
from dotenv import load_dotenv

load_dotenv(dotenv_path=f"envs/.env.paytm")
from paytmchecksum import PaytmChecksum

PAYTM_MERCHANT_ID = str(os.getenv("PAYTM_MERCHANT_ID"))
PAYTM_MERCHANT_KEY = str(os.getenv("PAYTM_MERCHANT_KEY"))
PAYTM_WEBSITENAME = str(os.getenv("PAYTM_WEBSITENAME"))
PAYTM_BASE_URL = str(os.getenv("PAYTM_BASE_URL"))
PAYTM_TRANSACTION_URL_SUFFIX = str(os.getenv("PAYTM_TRANSACTION_URL_SUFFIX"))
PAYTM_TRANSACTION_STATUS_URL_SUFFIX = str(
    os.getenv("PAYTM_TRANSACTION_STATUS_URL_SUFFIX")
)

PAYTM_TRANSACTION_URL = "{}{}".format(PAYTM_BASE_URL, PAYTM_TRANSACTION_URL_SUFFIX)
PAYTM_TRANSACTION_STATUS_URL = "{}{}".format(
    PAYTM_BASE_URL, PAYTM_TRANSACTION_STATUS_URL_SUFFIX
)


class PaytmAPIWrapper:
    def __init__(self):
        self.transaction_url = PAYTM_TRANSACTION_URL
        self.transaction_status_url = PAYTM_TRANSACTION_STATUS_URL
        self.merchant_id = PAYTM_MERCHANT_ID
        self.merchant_key = PAYTM_MERCHANT_KEY
        self.website_name = PAYTM_WEBSITENAME
        self.base_url = PAYTM_BASE_URL

        self.transaction_token = None
        self.request = None
        self.callback_url = None
        self.response = None

        logging.debug(f"PAYTM_BASE_URL: {self.base_url}")
        logging.debug(f"PAYTM_TRANSACTION_URL: {self.transaction_url}")
        logging.debug(f"PAYTM_TRANSACTION_STATUS_URL: {self.transaction_status_url}")
        logging.debug(f"PAYTM_MERCHANT_ID: {self.merchant_id}")

    def get_data(self, endpoint, params=None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params)
        return response.json()
        # Process the response and return data

    def post_data(self, endpoint, data=None, add_checksum=True):
        if add_checksum:
            checksum = PaytmChecksum.generateSignature(
                json.dumps(data["body"]), self.merchant_key
            )
            data["head"] = {"signature": checksum}

        url = f"{self.base_url}{endpoint}"
        logging.debug(f"POSTing to {url}")
        logging.debug(f"POST data: {data}")
        response = requests.post(
            url, json=data, headers={"Content-type": "application/json"}
        )
        logging.debug(f"POST response: {response}")
        return response.json()
