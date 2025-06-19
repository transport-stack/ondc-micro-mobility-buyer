from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.serializers import TransitModeField, TransitModeMixinSerializer
from transit.models.transit_setup import TransitOption, TransitProvider
from transit.models.trip_setup import Trip

"""
Serializers
"""


class TripSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField("get_status")
    transit_mode = TransitModeField()

    @extend_schema_field(serializers.CharField)
    def get_status(self, obj):
        return obj.get_status()

    class Meta:
        model = Trip
        fields = "__all__"


class SingleTripSerializer(serializers.ModelSerializer):
    transit_option = serializers.SerializerMethodField("get_transit_option")

    def get_transit_option(self, obj):
        if obj.transit_option:
            return TransitOptionSerializer(obj.transit_option).data
        else:
            return None

    class Meta:
        model = Trip
        fields = "__all__"


class MultiTripSerializer(serializers.ModelSerializer):
    transit_option = serializers.SerializerMethodField("get_transit_option")
    children = serializers.SerializerMethodField("get_children")

    def get_transit_option(self, obj):
        if obj.transit_option:
            return TransitOptionSerializer(obj.transit_option).data
        else:
            return None

    def get_children(self, obj):
        return SingleTripSerializer(obj.get_children(), many=True).data

    class Meta:
        model = Trip
        fields = "__all__"


# add serializer for TransitProvider
class TransitProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransitProvider
        fields = ["name"]


# add serializer for TransitOption
class TransitOptionSerializer(TransitModeMixinSerializer):
    provider = TransitProviderSerializer()

    class Meta:
        model = TransitOption
        exclude = ["active", "id"]
