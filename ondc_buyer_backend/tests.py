from rest_framework.test import APIClient
from unittest.mock import patch
import requests_mock
from rest_framework.test import APITestCase
from django.test import TestCase, RequestFactory, override_settings
from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase
from django.urls import reverse

@override_settings(X_API_KEY="test")
class TestTicketBookingProcess(SimpleUserTransitTestCase):

    def setUp(self):
        super().setUp()
    
    @requests_mock.Mocker()
    @patch('ondc_micromobility_api.wrapper.estimate.EstimateAPI.estimate_wrapper')
    @patch('django.core.cache.cache.get')
    @patch('django.core.cache.cache.set')
    def test_complete_ticket_booking_process(self, mocked_requests, mocked_estimate, mocked_cache_get, mocked_cache_set):

        # Setup Mock for the external API call
        mocked_estimate.return_value ={
                "message": "Success",
                "description": "Fare fetched successfully.",
                "data": {
                    "fare": {
                    "transaction_id": "69976055-f8c3-41d5-9646-0d5a78f2775a",
                    "data": [
                        {
                        "id": "I1",
                        "descriptor": {
                            "name": "102STLDOWN",
                            "code": "SJT-1",
                            "images": [
                            {
                                "url": "https://transitsolutions.in/logos/logo.icon",
                                "size_type": "xs"
                            }
                            ]
                        },
                        "fulfillment_ids": [
                            "F1"
                        ],
                        "price": {
                            "currency": "INR",
                            "value": "10.0"
                        },
                        "quantity": {
                            "maximum": {
                            "count": 1
                            },
                            "minimum": {
                            "count": 1
                            }
                        }
                        }
                    ]
                    },
                    "description": "Fare fetched successfully."
                }
                }

        # Mocking cache responses


        # Mock HTTP responses for transaction and confirmation
        mocked_requests.post('http://127.0.0.1:8000/api/v1/tickets/transaction/', json={'success': True})
        mocked_requests.post('http://127.0.0.1:8000/api/v1/tickets/confirm/', json={'ticket_id': 'ticket123'})

        # Start the process by simulating a user hitting the initiate endpoint
        initiate_data = {
                    "start_location_code": "ROHINI_SEC_22_TERMINAL",
                    "end_location_code": "AVANTIKA_XING",
                    "transit_option":
                        {
                            "transit_mode": "BUS",
                            "provider":
                                {
                                    "name": "ONDC"
                                }
                        },
                    "meta": {
                        "route_id": "102STLDOWN"
                    }
                }
        
        
        print("Initiate data============",initiate_data)
        response = self.client.post(
            reverse("tickets:ticket-initiate"), data=initiate_data, format="json"
        )
        self.pnr = response.data["pnr"]

        # Simulate transaction processing
        transaction_response = self.client.post('/api/v1/tickets/transaction/', data={'pnr': self.pnr})
        self.assertTrue(transaction_response.data['success'])

        # Simulate ticket confirmation
        confirm_response = self.client.post('/api/v1/tickets/confirm/', data={'pnr': self.pnr})
        self.assertEqual(confirm_response.data['ticket_id'], 'ticket123')

        # Assertions to ensure the flow was correct
        self.assertEqual(mocked_cache_set.call_count, 2)  

