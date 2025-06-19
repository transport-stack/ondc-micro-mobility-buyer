from rest_framework import serializers

from custom_cities.models import City


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        exclude = ("id",)
