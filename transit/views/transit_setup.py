from modules.views import BaseViewSet, CustomJSONRenderer
from transit.models.transit_setup import TransitOption, TransitProvider
from transit.serializers import TransitOptionSerializer, TransitProviderSerializer


class TransitProviderViewSet(BaseViewSet):
    queryset = TransitProvider.objects.all()
    serializer_class = TransitProviderSerializer
    lookup_field = "id"
    model = TransitProvider


class TransitOptionViewSet(BaseViewSet):
    queryset = TransitOption.objects.all()
    serializer_class = TransitOptionSerializer
    lookup_field = "id"
    model = TransitOption
