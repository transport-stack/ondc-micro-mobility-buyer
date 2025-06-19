from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from coupons.models import Coupon
from tickets.tests.integration.test_base_setup import BasicTestCase


class CouponTests(BasicTestCase):

    def setUp(self):
        super().setUp()

        # Create multiple coupons
        self.coupon1 = Coupon.objects.create(
            code="TESTCOUPON1",
            description="Test Coupon 1",
            valid_from="2023-01-01T00:00Z",
            max_discount_amount=100.0,
            max_discount_percent=10.0,
            is_visible=True,
            active=True
        )

        self.coupon2 = Coupon.objects.create(
            code="TESTCOUPON2",
            description="Test Coupon 2",
            valid_from="2023-01-02T00:00Z",
            max_discount_amount=50.0,
            max_discount_percent=5.0,
            is_visible=False,  # This coupon is invisible but active
            active=True
        )

        self.coupon3 = Coupon.objects.create(
            code="TESTCOUPON3",
            description="Test Coupon 3",
            valid_from="2023-01-03T00:00Z",
            max_discount_amount=150.0,
            max_discount_percent=15.0,
            is_visible=True,
            active=False  # This coupon is visible but inactive
        )

    def test_list_coupons(self):
        # Call the API to list all coupons
        response = self.client.get(
            reverse('coupon-list'))  # Assuming 'coupon-list' is the name of the URL pattern for listing coupons

        # Check the response status
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check if the visible and active coupons are returned
        self.assertIn(self.coupon1.code, str(response.data))

        # Check if the invisible but active coupon is NOT returned
        self.assertNotIn(self.coupon2.code, str(response.data))

        # [Optional] Check if the visible but inactive coupon is NOT returned
        self.assertNotIn(self.coupon3.code, str(response.data))
