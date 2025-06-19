from rest_framework import serializers

from coupons.models import Coupon


class CouponCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ("code",)


class CouponSerializer(CouponCodeSerializer):
    class Meta:
        model = Coupon
        fields = ("code", "name", "description", "valid_till")
        read_only_fields = ("code", "name", "description", "valid_till")
