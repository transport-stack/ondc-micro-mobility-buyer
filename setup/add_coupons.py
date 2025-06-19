import logging
from datetime import datetime

from django.db import IntegrityError

from coupons.models import Coupon
from custom_cities.models import City

logger = logging.getLogger(__name__)


def add_coupons():
    coupons = [
        {
            "code": "FIRSTFREE",
            "active": True,
            "name": "FIRSTFREE",
            "description": "First Free",
            "valid_from": datetime.now(),
            "max_discount_amount": 15.0,
            "max_discount_percent": 50.0,
        },
        {
            "code": "WELCOME10",
            "active": True,
            "name": "WELCOME10",
            "description": "10 percent discount from Seller",
            "valid_from": datetime.now(),
            "max_discount_amount": 5.0,
            "max_discount_percent": 10.0,
        },
    ]

    for coupon_data in coupons:
        try:
            coupon, created = Coupon.objects.get_or_create(**coupon_data)
            logger.info(f"City {coupon_data['code']} created")
        except IntegrityError:
            logger.info(f"City {coupon_data['code']} already exists")
