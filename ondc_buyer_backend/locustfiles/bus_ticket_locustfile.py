import datetime
import random
import sqlite3
import time

import gevent

from locust import HttpUser, task, between, SequentialTaskSet


class Tasks(SequentialTaskSet):
    def __init__(self, parent):
        super().__init__(parent)
        self.API_KEY = 'test'
        self.transaction_id = None
        self.transaction_id_in_estimate = None
        self.success_received = False
        self.token = None
        self.headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.API_KEY
        }
        self.time_taken = []
        self.pnr = None
        self.gateway_order_id = None
        self.wait_time = between(1, 4)

    def on_start(self):
        print(f'time - on_start : {datetime.datetime.now()}')
        payload = {
            "transaction_id": self.transaction_id,
            "start_stop_code": "WEST_ENCLAVE_SANSAD_VIHAR_T",
            "end_stop_code": "DEV_NAGAR",
            "route_id": "993DOWN",
            "variant": "ac",
            "bus_reg_num": "DL1PD5604",
            "category": "P"
        }
        response = self.client.post("api/v1/ondc/delhi/bus/estimate", json=payload, headers=self.headers)
        if response.status_code == 200:
            estimate_data = response.json().get('data', {}).get('fare', {})
            self.transaction_id_in_estimate = estimate_data.get('transaction_id')
        self.success_received = False

    @task
    def estimate(self):
        print(f'time - estimate : {datetime.datetime.now()}')
        try:
            payload = {
                "transaction_id": self.transaction_id_in_estimate,
                "start_stop_code": "WEST_ENCLAVE_SANSAD_VIHAR_T",
                "end_stop_code": "DEV_NAGAR",
                "route_id": "993DOWN",
                "variant": "ac",
                "bus_reg_num": "DL1PD5604",
                "category": "P"
            }
            response = self.client.post("api/v1/ondc/delhi/bus/estimate", json=payload, headers=self.headers)
            if response.status_code == 200:
                fare = response.json().get('data', {}).get('fare')
                print(f'fare: {fare}')
            self.wait()

        except Exception as e:
            print(f"Exception in estimate: {str(e)}")

    @task
    def login(self):
        print(f'time - login : {datetime.datetime.now()}')
        try:
            payload = {
                "username": "rajan"
            }
            response = self.client.post("api/v1/accounts/user/login/", json=payload, headers=self.headers)
            if response.status_code == 200:
                print(f'response : {response.json()}')
                self.token = response.json().get('data', {}).get('access_token', {})
                self.headers = {
                    'Content-Type': 'application/json',
                    'x-api-key': self.API_KEY,
                    'Authorization': f'Bearer {self.token}'
                }
                gevent.spawn_later(2, self.initiate)
            else:
                print(response.json())
                print(f"Login failed, status code: {response.status_code}")
            self.wait()

        except Exception as e:
            print(f"Exception in login: {str(e)}")

    def initiate(self):
        print(f'time - initiate : {datetime.datetime.now()}')
        try:
            payload = {
                "transaction_id": self.transaction_id_in_estimate,
                "ticket_count": 1,
                "transit_option": {
                    "transit_mode": "BUS",
                    "provider": {
                        "name": "ONDC"
                    }
                },
                "meta": {
                    "route_id": "993DOWN",
                    "variant": "ac",
                    "bus_reg_num": "DL1PD5604"
                }
            }
            response = self.client.post("api/v1/tickets/initiate/", json=payload, headers=self.headers)
            if response.status_code != 200:
                print(f'initiate : {response.status_code}')
            self.pnr = response.json().get('data').get('pnr')
        except Exception as e:
            print(f"Exception in initiate: {str(e)}")

    @task
    def transaction(self):
        self.headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.API_KEY,
            'Authorization': f'Bearer {self.token}'
        }
        TRANSACTION_URL = f"api/v1/tickets/{{}}/transaction/"
        data = {"payment_mode": "UNKNOWN"}
        url = TRANSACTION_URL.format(self.pnr)
        response = self.client.post(url, json=data, headers=self.headers)
        self.gateway_order_id = response.json().get('data').get('gateway_order_id')

    @task
    def confirm(self):
        self.headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.API_KEY,
            'Authorization': f'Bearer {self.token}'
        }
        CONFIRM_URL = f"api/v1/tickets/{{}}/confirm/"
        url = CONFIRM_URL.format(self.pnr)
        response = self.client.get(url, headers=self.headers)
        print(f"Ticket created==========={response.json()}")

    def wait(self):
        time.sleep(self.wait_time(self))


class MyUser(HttpUser):
    tasks = [Tasks]
    wait_time = between(2, 5)