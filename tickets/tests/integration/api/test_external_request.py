import responses
import requests
from unittest import TestCase


class TestMyAPI(TestCase):

    @responses.activate
    def test_my_api(self):
        responses.add(responses.POST, 'https://customer.staging.plectrum.dev/b2c/api/v1.0/cancel', json={}, status=200)
        resp = requests.post('https://customer.staging.plectrum.dev/b2c/api/v1.0/cancel')
        print(resp.json())
        # # Mocking the abc.com request
        # responses.add(responses.GET, 'http://139.59.70.21:9875/bus-route?vid=DL1PC5335',
        #               json=[{"id": "DL1PC5335", "route_name": None, "route_id": None}], status=200)
        #
        # # Mocking the xyz.com request
        # responses.add(responses.GET, 'http://139.59.9.136:9900/api/v2/bus_and_duty_gtfs_routes/',
        #               json={"DL1PC0243": [], "DL1PC5335": ["427DOWN", "427UP"], "DL1PC5336": [], "DL1PC5338": [],
        #                     "DL1PC5339": [], "DL1PC9997": ["970DOWN", "970UP", "114+990DOWN", "990CLDOWN", "990CLUP"]},
        #               status=200)
        #
        # resp_bus_route = requests.get('http://139.59.70.21:9875/bus-route?vid=DL1PC5335')
        # self.assertEqual(resp_bus_route.json(), [{"id": "DL1PC5335", "route_name": None, "route_id": None}])
        #
        # resp_gtfs_routes = requests.get('http://139.59.9.136:9900/api/v2/bus_and_duty_gtfs_routes/')
        # self.assertEqual(resp_gtfs_routes.json(),
        #                  {"DL1PC0243": [], "DL1PC5335": ["427DOWN", "427UP"], "DL1PC5336": [], "DL1PC5338": [],
        #                   "DL1PC5339": [], "DL1PC9997": ["970DOWN", "970UP", "114+990DOWN", "990CLDOWN", "990CLUP"]})

    @responses.activate
    def test_paytm_initiate_transaction(self):
        # Mock the endpoint
        responses.add(
            responses.GET,
            "https://securegw-stage.paytm.in/theia/api/v1/initiateTransaction",
            json={"success": True, "message": "Transaction initiated successfully"},
            status=200,
        )

        # Perform your test (using the requests library)
        response = requests.get(
            "https://securegw-stage.paytm.in/theia/api/v1/initiateTransaction?mid=OneDel75778312891699&orderId=231029093950NIDF9BWQD")

        # Asserts
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": True, "message": "Transaction initiated successfully"})
