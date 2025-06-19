import datetime
from unittest.mock import patch

import responses
from django.urls import reverse

from coupons.models import Coupon
from tickets.models import Ticket
from tickets.tests.integration.test_base_setup import SimpleUserTransitTestCase


class TicketInitiateTest(SimpleUserTransitTestCase):
    def setUp(self):
        super().setUp()
        # add coupon object
        """
        code
        name
        description
        valid_from
        valid_till
        max_discount_amount
        max_discount_percent
        """
        self.coupon_code = "TESTCOUPON"
        self.coupon = Coupon.objects.filter(code=self.coupon_code)
        if not self.coupon.exists():
            self.coupon = Coupon.objects.create(
                code=self.coupon_code,
                name="Test Coupon",
                description="Test Coupon",
                max_discount_amount=10,
                max_discount_percent=100,
                valid_from=datetime.datetime.now(),
                valid_till=datetime.datetime.now() + datetime.timedelta(days=100),
            )

    def test_ticket_apply_coupon(self):
        # make initiate request
        self.init_response = self.initiate_ticket()
        self.pnr = self.init_response.data["pnr"]

        # apply coupon
        request_data = {"code": self.coupon_code}
        response = self.client.post(
            reverse("tickets:ticket-apply-coupon", kwargs={"pk": self.pnr}),
            data=request_data,
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # test ticket's fare object
        ticket_obj = Ticket.objects.filter(pnr=self.pnr).first()
        self.assertIsNotNone(ticket_obj.fare.coupon)
        self.assertTrue(ticket_obj.fare.coupon_discount > 0)

    def test_ticket_unapply_coupon(self):
        # make initiate request
        self.init_response = self.initiate_ticket()
        self.pnr = self.init_response.data["pnr"]

        # apply coupon
        request_data = {"code": self.coupon_code}
        response = self.client.post(
            reverse("tickets:ticket-apply-coupon", kwargs={"pk": self.pnr}),
            data=request_data,
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # unapply coupon
        request_data = {}
        response = self.client.post(
            reverse("tickets:ticket-unapply-coupon", kwargs={"pk": self.pnr}),
            data=request_data,
            format="json",
        )
        self.assertEqual(response.status_code, 200)

        # test ticket's fare object
        ticket_obj = Ticket.objects.filter(pnr=self.pnr).first()
        self.assertIsNone(ticket_obj.fare.coupon)
        self.assertTrue(ticket_obj.fare.coupon_discount == 0)
