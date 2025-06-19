import uuid

from django.test import TestCase
from django.utils import timezone

from accounts.models.user_setup import MyUser
from modules.constants import RAPIDO_ENUM
from modules.models import TransitMode, TripStatus
from transit.models.transit_setup import TransitOption, TransitProvider
from transit.models.trip_setup import Trip


class TripTestCase(TestCase):
    def setUp(self):
        self.user = MyUser.objects.create(username="testuser")
        # Create a transit provider for RAPIDO
        self.rapido_provider, _ = TransitProvider.objects.get_or_create(
            name=RAPIDO_ENUM
        )

        # Create transit options for RAPIDO
        self.bike_option, _ = TransitOption.objects.get_or_create(
            provider=self.rapido_provider, transit_mode=TransitMode.BIKE.value
        )
        self.auto_option, _ = TransitOption.objects.get_or_create(
            provider=self.rapido_provider, transit_mode=TransitMode.AUTO_RICKSHAW.value
        )

        self.transit_option = self.bike_option

    def test_trip_creation(self):
        trip = Trip.objects.create(user=self.user, transit_option=self.transit_option)
        self.assertIsNotNone(trip.uuid)
        self.assertTrue(isinstance(trip.uuid, uuid.UUID))

    def test_parent_child_relationship(self):
        parent_trip = Trip.objects.create(
            user=self.user, transit_option=self.transit_option
        )
        child_trip = Trip.objects.create(
            user=self.user, transit_option=self.transit_option, parent=parent_trip
        )
        self.assertEqual(child_trip.get_parent(), parent_trip)
        self.assertTrue(parent_trip.get_children().exists())

    def test_foreign_key_relationships(self):
        trip = Trip.objects.create(user=self.user, transit_option=self.transit_option)
        self.assertEqual(trip.user, self.user)
        self.assertEqual(trip.transit_option, self.transit_option)

    def test_scheduled_and_actual_time(self):
        now = timezone.now()
        trip = Trip.objects.create(
            user=self.user,
            transit_option=self.transit_option,
            scheduled_start_datetime=now,
            actual_start_datetime=now,
        )
        self.assertEqual(trip.scheduled_start_datetime, now)
        self.assertEqual(trip.actual_start_datetime, now)

    def test_get_status(self):
        trip1 = Trip.objects.create(user=self.user, transit_option=self.transit_option)
        trip2 = Trip.objects.create(
            user=self.user,
            transit_option=self.transit_option,
            actual_start_datetime=timezone.now(),
        )
        trip3 = Trip.objects.create(
            user=self.user,
            transit_option=self.transit_option,
            actual_start_datetime=timezone.now(),
            actual_end_datetime=timezone.now(),
        )
        self.assertEqual(trip1.get_status(), TripStatus.SCHEDULED.name)
        self.assertEqual(trip2.get_status(), TripStatus.ONGOING.name)
        self.assertEqual(trip3.get_status(), TripStatus.COMPLETED.name)

    def test_get_transit_mode(self):
        trip = Trip.objects.create(user=self.user, transit_option=self.transit_option)
        self.assertEqual(trip.get_transit_mode(), trip.transit_mode)

    def test_duration_and_distance(self):
        trip = Trip.objects.create(
            user=self.user,
            transit_option=self.transit_option,
            duration=3600,
            distance=1000,
        )
        self.assertEqual(trip.duration, 3600)
        self.assertEqual(trip.distance, 1000)

    def test_fare(self):
        trip = Trip.objects.create(
            user=self.user, transit_option=self.transit_option, fare=50.0
        )
        self.assertEqual(trip.fare, 50.0)

    def test_string_representation(self):
        trip = Trip.objects.create(user=self.user, transit_option=self.transit_option)
        self.assertEqual(str(trip), f"{trip.uuid} # {trip.transit_mode.__str__()}")
