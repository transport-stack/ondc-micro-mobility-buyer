from django.urls import reverse
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from ondc_micromobility_api.models import MetroStation, FareMatrix, SystemParameters


class SystemParametersSerializer(serializers.ModelSerializer):
    metro_station_url_path = serializers.SerializerMethodField()

    class Meta:
        model = SystemParameters
        fields = ['metro_station_url_path', 'qr_label_message', 'max_passengers_per_ticket', 'service_enabled',
                  'service_message']

    @extend_schema_field(serializers.CharField)
    def get_metro_station_url_path(self, obj):
        # Assuming 'metro-stations' is the name of the URL pattern for fetching metro stations
        base_url = reverse('ondc_micromobility_api:metro-station-list')
        return f"{base_url}?last_modified={obj.metro_stations_last_modified}"


class MetroStationSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetroStation
        exclude = ['created_at', 'updated_at', 'active', 'location']


class FareMatrixSerializer(serializers.ModelSerializer):
    source_station = MetroStationSerializer()
    destination_station = MetroStationSerializer()

    class Meta:
        model = FareMatrix
        exclude = ['created_at', 'updated_at', 'active']


class EstimateRequestSerializer(serializers.Serializer):
    Src_Stn = serializers.CharField()
    Dest_Stn = serializers.CharField()


class EstimateResponseSerializer(serializers.Serializer):
    fare = serializers.IntegerField()
    description = serializers.CharField()

#
# class BookRequestSerializer(serializers.Serializer):
#     user = RapidoUserSerializer()
#     pickupLocation = RapidoLocationSerializer()
#     dropLocation = RapidoLocationSerializer()
#     serviceType = serializers.ChoiceField(choices=SERVICE_TYPE_CHOICES)
#
