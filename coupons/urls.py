from django.urls import path, include
from rest_framework import routers

from coupons.views import CouponViewSet

from modules.views import NoSlashRouter

router = NoSlashRouter()

router.register(r"", CouponViewSet, "coupon")

urlpatterns = [
    path("", include(router.urls)),
]
