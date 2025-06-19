from custom_cities.models import City
from custom_cities.serializers import CitySerializer
from modules.views import BaseViewSet, CustomJSONRenderer


class CityViewSet(BaseViewSet):
    queryset = City.objects.all()
    serializer_class = CitySerializer
    lookup_field = "code"
    model = City
