import datetime

import pytz
from rest_framework import serializers

from modules.time_helpers import get_ist_time_given_epoch_time
from nammayatri.constants import SERVICE_TYPE_CHOICES


class NammayatriUserSerializer(serializers.Serializer):
    mobile = serializers.CharField(max_length=10)

    def validate_mobile(self, value):
        """Check that the mobile number is numeric and has exactly 10 digits."""
        if not value.isdigit():
            raise serializers.ValidationError("Mobile number must be numeric.")
        if len(value) != 10:
            raise serializers.ValidationError(
                "Mobile number must have exactly 10 digits."
            )
        return value


class NammayatriLocationSerializer(serializers.Serializer):
    lat = serializers.FloatField(allow_null=True)
    lng = serializers.FloatField(allow_null=True)


class NammayatriLocationSerializer2(serializers.Serializer):
    latitude = serializers.FloatField(allow_null=True)
    longitude = serializers.FloatField(allow_null=True)


class BookRequestSerializer(serializers.Serializer):
    transaction_id = serializers.UUIDField()
    user = NammayatriUserSerializer()
    pickupLocation = NammayatriLocationSerializer()
    dropLocation = NammayatriLocationSerializer()
    serviceType = serializers.ChoiceField(choices=SERVICE_TYPE_CHOICES)


class CancelRequestSerializer(serializers.Serializer):
    transaction_id = serializers.UUIDField()
    cancelReason = serializers.CharField(max_length=255)


class EstimateRequestSerializer(serializers.Serializer):
    pickupLocation = NammayatriLocationSerializer()
    dropLocation = NammayatriLocationSerializer()
    serviceType = serializers.ListField(child=serializers.CharField())


"""
  "captainDetails": {   
      "name": "Harry Potter",
      "currentVehicle": {
          "number": "ADSDSD"
      },
      "mobile": "1234567890"
  },
"""


class CurrentVehicleSerializer(serializers.Serializer):
    number = serializers.CharField(max_length=20)


class CaptainDetailsSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    mobile = serializers.CharField(max_length=15)
    currentVehicle = CurrentVehicleSerializer(allow_null=True)


class OrderUpdateSerializer(serializers.Serializer):
    orderId = serializers.CharField(max_length=128, required=False)
    status = serializers.CharField(max_length=128, required=False)
    metadata = serializers.DictField(child=serializers.CharField(), required=False)
    eta = serializers.FloatField(allow_null=True, required=False)
    captainDetails = CaptainDetailsSerializer(allow_null=True, required=False)
    otp = serializers.CharField(max_length=10, allow_null=True, required=False)
    amount = serializers.FloatField(allow_null=True, required=False)
    distanceTravelled = serializers.FloatField(allow_null=True, required=False)
    travelDuration = serializers.FloatField(allow_null=True, required=False)
    dropTime = serializers.IntegerField(allow_null=True, required=False)


class LocationUpdateSerializer(serializers.Serializer):
    """
    {
            "status": "arrived",
            "location": {
                "latitude": 12.917401377481589,
                "longitude": 77.6224747672677
            },
            "timestamp": 1618420912065,
            "order_id": "08c77c6d-c9ec-4958-a63e-16d4599fce00"
        }
    ]
    """

    order_id = serializers.CharField(max_length=128, required=True)
    status = serializers.CharField(max_length=128, required=False)
    location = NammayatriLocationSerializer2(required=True)
    timestamp = serializers.IntegerField(allow_null=True, required=False)
    # Add the field for the ISO formatted datetime
    timestamp_iso = serializers.SerializerMethodField()

    def get_timestamp_iso(self, obj):
        """
        Convert the epoch timestamp to ISO formatted datetime.
        """
        if obj.get("timestamp"):
            return get_ist_time_given_epoch_time(obj["timestamp"] / 1000.0).isoformat()
        return None


class PatchCallToCustomerSerializer(serializers.Serializer):
    """
    {
            "order_id": "xxxxxxxxxx",
            "driver_no": "xxxxxxxxxx",
        }
    ]
    """

    order_id = serializers.CharField(max_length=128, required=True)
    driver_no = serializers.CharField(max_length=128, required=False)
