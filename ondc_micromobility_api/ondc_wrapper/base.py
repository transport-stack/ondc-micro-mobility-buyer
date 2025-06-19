import datetime
import json
import logging
import os
from typing import Union

import requests
from django.core.cache import cache
from dotenv import load_dotenv

# from ondc_micromobility_api.dmrc_wrapper.utils.signature_setup import sign_with_rsa_key

load_dotenv(dotenv_path=f"envs/.env.ondc")


class APIClientBase:
    SUCCESS_TEXT = "Success"
    SELLER_KEY = str(os.getenv("DMRC_SELLER_KEY"))
    REQUESTER_ID = SELLER_KEY
    OPERATOR_ID = 2
    OPERATOR_ID_STR = str(OPERATOR_ID)
    BASE_URL = os.getenv("DMRC_BASE_URL")
    HEADERS = {"accept": "*/*", "Content-Type": "application/json"}

    TOKEN_CACHE_KEY = 'dmrc_thales_api_client_base_token'
    TOKEN_CACHE_TIMEOUT = 3600 * 24  # 24 hours

    def __init__(self, token=None, signature_key_name=None):
        self.token = token or self.get_or_generate_token()
        self.signature_key_name = signature_key_name
        self.current_datetime_formatted_str = datetime.datetime.now().strftime(
            "%d/%m/%Y@%H-%M-%S"
        )

    def set_authorization(self):
        if self.token:
            self.HEADERS["Authorization"] = f"Bearer {self.token}"

    def generate_signature(self, data: str) -> str:
        data = data.replace(" ", "")
        logging.debug(data)
        # signature = sign_with_rsa_key(data)
        # logging.debug(f"Signature: {signature}\n")
        # return signature

    def get_access_token(self):
        value = "{}.{}".format(
            self.SELLER_KEY, datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        )
        signature = self.generate_signature(value)
        payload = {"sellerKey": value, "Signature": signature}

        headers = {"accept": "*/*", "Content-Type": "application/json"}
        if self.BASE_URL is not None:
            url = f"{self.BASE_URL}/GenerateToken"
            response = requests.post(url, headers=headers, json=payload)
            logging.debug(f"Response: \n{json.dumps(response.json(), indent=2)}\n")
            token = response.json()["token"]["access_token"]
            logging.debug(f"Token: \n{token}")
            return token
        else:
            return None

    def get_or_generate_token(self):
        cached_token = cache.get(self.TOKEN_CACHE_KEY)

        if cached_token:
            return cached_token

        # Generate a new token if not found in cache or expired
        new_token = self.get_access_token()
        # assert new_token and new_token.strip() != "", "Invalid token received"
        cache.set(self.TOKEN_CACHE_KEY, new_token, self.TOKEN_CACHE_TIMEOUT)

        return new_token

    def post(self, endpoint: str, payload: dict) -> dict:
        self.set_authorization()
        url = f"{self.BASE_URL}/{endpoint}"
        logging.debug(f"POST {url}")
        # logging.debug(self.HEADERS)
        logging.debug(payload)
        response = requests.post(url, headers=self.HEADERS, json=payload)

        if response.status_code == 401:  # Unauthorized
            cache.delete(self.TOKEN_CACHE_KEY)
            self.token = self.get_or_generate_token()
            self.set_authorization()
            response = requests.post(url, headers=self.HEADERS, json=payload)

        response_json = response.json()
        logging.debug(f"Response: \n{json.dumps(response_json, indent=2)}\n")
        return response_json

    def get(self, endpoint: str, params=None) -> dict:
        self.set_authorization()
        url = f"{self.BASE_URL}/{endpoint}"
        logging.debug(f"GET {url}")
        response = requests.get(url, headers=self.HEADERS, params=params)

        if response.status_code == 401:  # Unauthorized
            cache.delete(self.TOKEN_CACHE_KEY)
            self.token = self.get_or_generate_token()
            self.set_authorization()
            response = requests.get(url, headers=self.HEADERS, params=params)

        response_json = response.json()
        logging.debug(f"Response: \n{json.dumps(response_json, indent=2)}\n")
        return response_json

    def validate_response(self, data: dict) -> Union[object, None]:
        """
        This method should be implemented in the child class to
        validate the response.
        """
        raise NotImplementedError(
            "validate_response method should be implemented in child class."
        )

# class GenerateTokenAPI(APIClientBase):
#     def get_access_token(self):
#         value = "{}.{}".format(
#             self.SELLER_KEY, datetime.datetime.now().strftime("%Y%m%d%H%M%S")
#         )
#         signature = self.generate_signature(value)
#         payload = {"sellerKey": value, "Signature": signature}
#         response = self.post("GenerateToken", payload)
#         token = response["token"]["access_token"]
#         logging.debug(f"Token: \n{token}")
#         return token
