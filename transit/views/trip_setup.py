from modules.views import BaseViewSet, CustomJSONRenderer
from transit.models.trip_setup import Trip
from transit.serializers import TripSerializer

"""
add following views

trips/
trips/<trip_id>/
trips/<trip_id>/start/
trips/<trip_id>/stop/
"""


class TripViewSet(BaseViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    lookup_field = "uuid"
    model = Trip


def get_trips(user_obj):
    """
    get all trips for a user
    """
    pass


def get_trip(trip_id):
    """
    get a trip
    """
    pass


def start_trip(request, trip_id):
    """
    start a trip for a user
    """
    pass


def stop_trip(request, trip_id):
    """
    stop a trip for a user
    """
    pass
