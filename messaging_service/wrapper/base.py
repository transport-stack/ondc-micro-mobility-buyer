import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


class MessagingServiceWrapper:
    def __init__(self):
        SMS_BASE_URL = os.getenv("SMS_BASE_URL")
        SMS_API_KEY = os.getenv("SMS_API_KEY")
        self.base_url = SMS_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {SMS_API_KEY}",
        }

    def send_otp(self, phone_number):
        url = f"{self.base_url}/create/{phone_number}"
        response = requests.get(url, headers=self.headers)
        return response

    def verify_otp(self, phone_number, otp):
        url = f"{self.base_url}/verify/{phone_number}"
        self.headers["Content-Type"] = "application/json"
        payload = json.dumps({"otp": otp})
        response = requests.post(url, headers=self.headers, data=payload)
        return response


class MockMessagingServiceResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self.json_data = json_data or {}

    def json(self):
        return self.json_data
