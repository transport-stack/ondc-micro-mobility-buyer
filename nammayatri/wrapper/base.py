import logging
import os

import requests

# .env.rapido
RAPIDO_BASE_URL = os.getenv("RAPIDO_BASE_URL")
RAPIDO_API_KEY = os.getenv("RAPIDO_API_KEY")


class RapidoAPIWrapper:
    def __init__(self):
        self.base_url = RAPIDO_BASE_URL
        self.api_key = RAPIDO_API_KEY

        logging.info(f"RAPIDO_BASE_URL: {self.base_url}")

    def get_auth_headers(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "apiKey": self.api_key,
        }
        return headers

    def get_data(self, endpoint, params=None):
        headers = self.get_auth_headers()
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, headers=headers, params=params)
        logging.debug(f"GET {url}")
        logging.debug(f"GET {response.json()}")
        return response
        # Process the response and return data

    def post_data(self, endpoint, data=None):
        headers = self.get_auth_headers()
        url = f"{self.base_url}/{endpoint}"
        logging.debug(f"POST {url}")
        logging.debug(f"POST {data}")
        response = requests.post(url, headers=headers, json=data)
        logging.debug(f"POST {response.json()}")
        return response
        # Process the response and return data
