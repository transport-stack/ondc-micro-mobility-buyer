from unittest import skip
from unittest.mock import patch

from rest_framework import status
from django.urls import reverse

from rest_framework.test import APIRequestFactory, force_authenticate

from journey.models.journey_setup import Journey
from journey.views.journey_setup import JourneyViewSet
from tickets.tests.integration.test_base_setup import BasicTestCase


class JourneyGetManyTest(BasicTestCase):
    def setUp(self):
        super().setUp()
        self.factory = APIRequestFactory()
        self.view = JourneyViewSet.as_view({"get": "list"})
        self.url = "/api/v1/journey/"

        journey_data = {}
        # Create some Journey objects
        self.journey1 = Journey.objects.create(
            created_by=self.user,
            created_for=self.user,
            data=journey_data,
        )
        self.journey2 = Journey.objects.create(
            created_by=self.user,
            created_for=self.user,
            data=journey_data,
        )
        # Fill in the rest of the required fields above with dummy data

    @patch("modules.views.XAPIKeyPermission.has_permission", return_value=True)
    def test_get_journeys_without_ticket(self, _):
        request = self.factory.get(self.url)
        force_authenticate(
            request, user=self.user
        )  # Django REST Framework provides this function
        response = self.view(request)

        # response = view.get(request)
        # Check the HTTP status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the data returned
        # since we don't return journeys without tickets, the response should be empty
        self.assertEqual(len(list(response.data["results"])), 0)
        # self.assertEqual(
        #     response.data["results"][0]["uuid"], str(self.journey2.uuid)
        # )  # the latest journey should be the first
        # self.assertEqual(response.data["results"][1]["uuid"], str(self.journey1.uuid))

    @skip("TODO")
    @patch("modules.views.XAPIKeyPermission.has_permission", return_value=True)
    def test_get_journeys_with_ticket(self, _):
        # TODO: Create a ticket for each journey
        # TODO: Assert results
        request = self.factory.get(self.url)
        force_authenticate(
            request, user=self.user
        )  # Django REST Framework provides this function
        response = self.view(request)

        # response = view.get(request)
        # Check the HTTP status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check the data returned
        # since we don't return journeys without tickets, the response should be empty
        self.assertEqual(len(list(response.data["results"])), 2)
        self.assertEqual(
            response.data["results"][0]["uuid"], str(self.journey2.uuid)
        )  # the latest journey should be the first
        self.assertEqual(response.data["results"][1]["uuid"], str(self.journey1.uuid))

    def test_more_than_single_page_data(self):
        request = self.factory.get(
            "/api/v1/journey/"
        )  # You can replace '/' with your URL

        # Create 5 more Journey objects
        journey_data = {}
        self.journeys = [
            Journey.objects.create(
                created_by=self.user, created_for=self.user, data=journey_data
            )
            for _ in range(5)
        ]

        response = self.client.get(reverse("journey:journey-list"), format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list(response.data["results"])), 0)
        response = self.client.get(
            reverse("journey:journey-list"), {"page": 2}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # Test invalid page
        response = self.client.get(
            reverse("journey:journey-list"), {"page": 3}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
