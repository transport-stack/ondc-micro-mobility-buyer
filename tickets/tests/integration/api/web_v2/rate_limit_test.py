from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
import time

class RateLimitTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_post_rate_limit_on_initiate(self):
        # url = reverse('tickets:web_v2-initiate')
        url = "/web/api/v2/tickets/initiate/"
        payload = {}

        # Make 6 requests (should be allowed)
        for _ in range(6):
            response = self.client.post(url, payload, format='json')
            self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Make one more request (should be blocked)
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # Wait for 1 minute and try again (should be allowed)
        # Uncomment this to test
        # time.sleep(60)
        # response = self.client.post(url, payload, format='json')
        # self.assertNotEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
