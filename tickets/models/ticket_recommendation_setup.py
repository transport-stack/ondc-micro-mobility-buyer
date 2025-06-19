from django.conf import settings
from django.db import models

from accounts.models import MyUser
from modules.models import SourceDestinationLocationMixin, DateTimeMixin, ActiveMixin
from transit.models.transit_setup import TransitOption

IS_POSTGRESQL = False
if 'postgresql' in settings.DATABASES['default']['ENGINE']:
    IS_POSTGRESQL = True

class TicketRecommendation(SourceDestinationLocationMixin, DateTimeMixin, ActiveMixin):
    # user for whom it was created
    created_for = models.ForeignKey(
        MyUser,
        on_delete=models.CASCADE,
        related_name="created_for_ticket_recommendations",
        null=True,
        blank=True,
        db_index=True,
    )

    transit_option = models.ForeignKey(
        TransitOption,
        on_delete=models.CASCADE,
        related_name="ticket_recommendation_transit_options",
        db_index=True,
    )

    # Ranking or weightage of the recommendation
    # Higher the value, higher the weight
    weight = models.FloatField(
        default=0.0,
        help_text="Ranking or weightage for the recommendation",
        db_index=True,
    )

    @staticmethod
    def get_top_recommendations(user, start_location_code=None):
        recommendations_query = TicketRecommendation.objects.filter(
            created_for=user,
            active=True
        )

        if start_location_code:
            # Filter out the user's provided start location
            recommendations_query = recommendations_query.filter(start_location_code=None) \
                .exclude(end_location_code=start_location_code)
        else:
            # Consider only recommendations with both source and destination
            recommendations_query = recommendations_query.exclude(start_location_code=None)

        # Check if the database backend is PostgreSQL
        if IS_POSTGRESQL:
            # Use DISTINCT ON for PostgreSQL
            recommendations = recommendations_query.order_by('-weight')[:4]
        else:
            # Use Python filtering for other databases
            recommendations = []
            seen_destinations = set()
            for rec in recommendations_query.order_by('-weight'):
                if rec.end_location_code not in seen_destinations:
                    seen_destinations.add(rec.end_location_code)
                    recommendations.append(rec)
                if len(recommendations) == 4:
                    break

        return recommendations
