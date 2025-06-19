import datetime

from django.urls import reverse
from rest_framework import status

from journey.models import Journey
from journey.serializers.journey_setup import JourneySerializerMin
from tickets.tests.integration.test_base_setup import BasicTestCase


class JourneyViewSetTestCase(BasicTestCase):
    def setUp(self):
        super().setUp()
        print(type(self.client))
        print(self.client._credentials)

        # Sample data for journey creation
        self.journey_data = {"journey_data": "YOUR_SAMPLE_JOURNEY_DATA_HERE"}

        # Create a journey instance for testing retrieve and list
        self.journey = Journey.objects.create(
            created_by=self.user,
            created_for=self.user,
            data=self.journey_data,
            start_datetime=datetime.datetime.now(),
        )

    def test_create_journey(self):
        # Assuming you have a login method or endpoint to get the token.
        # Or you can use the authenticated client you set up in the setUp method.
        # self.client.login(username=self.username, password=self.password)

        # Get initial count of journeys
        initial_count = Journey.objects.count()

        # print self.client headers
        print(self.client._credentials)
        print(reverse("journey:journey-list"))

        # Post data to create a new journey
        response = self.client.post(
            reverse("journey:journey-list"), data=self.journey_data, format="json"
        )

        print(response.content)

        # Check the response
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Journey.objects.count(), initial_count + 1)

    def test_retrieve_journey(self):
        response = self.client.get(
            reverse("journey:journey-detail", args=[self.journey.uuid])
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # self.assertEqual(response.data, JourneySerializerMin(self.journey).data)

    def test_list_journeys(self):
        response = self.client.get(reverse("journey:journey-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("count" in response.data)
        self.assertTrue("next" in response.data)
        self.assertTrue("results" in response.data)
        self.assertTrue(isinstance(response.data["results"], list))

    def test_end_journey(self):
        response = self.client.post(
            reverse("journey:journey-end", args=[self.journey.uuid])
        )
        # because journeys with no ticket are not returned, we expect a 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Assert the journey is marked as completed (you might have a specific field or status to check)
        journey = Journey.objects.get(pk=self.journey.pk)
        # For instance, if you have an 'is_completed' field:
        # self.assertTrue(journey.is_completed)
