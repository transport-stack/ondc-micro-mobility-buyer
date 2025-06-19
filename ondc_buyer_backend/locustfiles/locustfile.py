import datetime
import time

import gevent
import json

import uuid
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
        with open('ondc_buyer_backend/routes.json', 'r') as f:
            self.requests = json.load(f)
        self.idx = 0
        self.estimate_resp = {}

    # def on_start(self):
    #     print(f'time - on_start : {datetime.datetime.now()}')
    #     request = self.requests[self.idx]
    #     request['transaction_id'] = self.transaction_id
    #     payload = request
    #     response = self.client.post("api/v1/ondc/delhi/bus/estimate", json=payload, headers=self.headers)
    #     if response.status_code == 200:
    #         estimate_data = response.json().get('data', {}).get('fare', {})
    #         self.transaction_id_in_estimate = estimate_data.get('transaction_id')
    #         self.estimate_resp[estimate_data.get('transaction_id')] = {'initiated': datetime.datetime.now()}
    #     self.success_received = False

    @task
    def estimate_1(self):
        print(f'time - estimate_1 : {datetime.datetime.now()}')
        request = self.requests[self.idx]
        request['transaction_id'] = self.transaction_id
        payload = request
        response = self.client.post("api/v1/ondc/delhi/bus/estimate", json=payload, headers=self.headers)
        if response.status_code == 200:
            estimate_data = response.json().get('data', {}).get('fare', {})
            self.transaction_id_in_estimate = estimate_data.get('transaction_id')
            self.estimate_resp[estimate_data.get('transaction_id')] = {'initiated': datetime.datetime.now()}
        self.success_received = False
        gevent.spawn_later(0.5, self.estimate)
        self.wait()

    @task
    def estimate(self):
        print(f'time - estimate : {datetime.datetime.now()}')
        try:
            request = self.requests[self.idx]
            request['transaction_id'] = self.transaction_id_in_estimate
            payload = request
            self.idx += 1
            # payload = {
            #     "transaction_id": self.transaction_id_in_estimate,
            #     "start_stop_code": "WEST_ENCLAVE_SANSAD_VIHAR_T",
            #     "end_stop_code": "DEV_NAGAR",
            #     "route_id": "993DOWN",
            #     "variant": "ac",
            #     "bus_reg_num": "DL1PD5604",
            #     "category": "G"
            # }
            response = self.client.post("api/v1/ondc/delhi/bus/estimate", json=payload, headers=self.headers)
            if response.status_code == 200:
                print(f'User {self.user.user_id} started with transaction_id: {self.transaction_id_in_estimate}')
                fare = response.json().get('data', {}).get('fare')
                self.estimate_resp[self.transaction_id_in_estimate]['received'] = datetime.datetime.now()
                print(self.estimate_resp[self.transaction_id_in_estimate])
                print(f"fare: {fare}' , 'time': {self.estimate_resp[self.transaction_id_in_estimate]['received'] - self.estimate_resp[self.transaction_id_in_estimate]['initiated']})")
                self.estimate_resp[self.transaction_id_in_estimate]['diff'] = (
                        self.estimate_resp[self.transaction_id_in_estimate]['received'] -
                        self.estimate_resp[self.transaction_id_in_estimate]['initiated'])
            self.wait()

        except Exception as e:
            print(f"Exception in estimate: {str(e)}")

    # @task
    # def login(self):
    #     print(f'time - login : {datetime.datetime.now()}')
    #     try:
    #         payload = {
    #             "username": "rajan"
    #         }
    #         response = self.client.post("api/v1/accounts/user/login/", json=payload, headers=self.headers)
    #         if response.status_code == 200:
    #             # print(f'response : {response.json()}')
    #             self.token = response.json().get('data', {}).get('access_token', {})
    #             self.headers = {
    #                 'Content-Type': 'application/json',
    #                 'x-api-key': self.API_KEY,
    #                 'Authorization': f'Bearer {self.token}'
    #             }
    #             # gevent.spawn_later(2, self.initiate)
    #         else:
    #             print(response.json())
    #             print(f"Login failed, status code: {response.status_code}")
    #         self.wait()
    #
    #     except Exception as e:
    #         print(f"Exception in login: {str(e)}")

    # @task
    # def initiate(self):
    #     print(f'time - initiate : {datetime.datetime.now()}')
    #     try:
    #         payload = {
    #             "transaction_id": self.transaction_id_in_estimate,
    #             "ticket_count": 1,
    #             "transit_option": {
    #                 "transit_mode": "BUS",
    #                 "provider": {
    #                     "name": "ONDC"
    #                 }
    #             },
    #             "meta": {
    #                 "route_id": "993DOWN",
    #                 "variant": "ac",
    #                 "bus_reg_num": "DL1PD5604"
    #             }
    #         }
    #         response = self.client.post("api/v1/tickets/initiate/", json=payload, headers=self.headers)
    #         if response.status_code != 200:
    #             print(f'initiate : {response.status_code}')
    #         self.pnr = response.json().get('data').get('pnr')
    #     except Exception as e:
    #         print(f"Exception in initiate: {str(e)}")

    def wait(self):
        time.sleep(self.wait_time(self))


class MyUser(HttpUser):
    tasks = [Tasks]
    wait_time = between(2, 5)

    def __init__(self, parent):
        super().__init__(parent)
        self.user_id = str(uuid.uuid4())