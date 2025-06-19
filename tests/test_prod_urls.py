import os
from unittest import skip

from django.test import SimpleTestCase
from django.urls import reverse, resolve


class TestDevURLs(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.environ['ENABLE_RAPIDO_WEBHOOK'] = 'True'

    @classmethod
    def tearDownClass(cls):
        del os.environ['ENABLE_RAPIDO_WEBHOOK']
        super().tearDownClass()

    @skip("TODO: enable this test")
    def test_rapido_url(self):
        url = reverse('rapido_api:location-update')
        self.assertEqual(resolve(url).namespace, 'rapido_api')

        url = reverse('rapido_api:order-update-internal')
        self.assertEqual(resolve(url).namespace, 'rapido_api')

        url = reverse('rapido_api:order-update')
        self.assertEqual(resolve(url).namespace, 'rapido_api')
