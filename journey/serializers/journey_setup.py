from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from journey.models.journey_setup import Journey
from modules.models import JourneyStatus, TicketStatus
from tickets.serializers import TicketSerializerMin

from rest_framework import serializers


class JourneyStatusRepresentationMixin(serializers.ModelSerializer):
    def get_status(self, obj) -> str:
        return obj.get_status_display()

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        status_name = instance.get_status_display()
        ret["status"] = status_name
        return ret

    def to_internal_value(self, data):
        try:
            status_name = data["status"]
            status_value = JourneyStatus[status_name.upper()].value
            data["status"] = status_value
            return super().to_internal_value(data)
        except KeyError:
            raise serializers.ValidationError({"status": "This status is not valid"})


class JourneySerializer(JourneyStatusRepresentationMixin):
    tickets = (
        serializers.SerializerMethodField()
    )  # TicketSerializerMin(many=True, read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Journey
        fields = ("created_at", "uuid", "data", "status", "tickets")

    @extend_schema_field(TicketSerializerMin(many=True))
    def get_tickets(self, obj):
        tickets = obj.tickets.filter(
            status__in=[
                TicketStatus.CONFIRMED,
                TicketStatus.PENDING,
                TicketStatus.EXPIRED,
            ]
        )
        serializer = TicketSerializerMin(tickets, many=True)
        return serializer.data


class JourneySerializerMin(JourneyStatusRepresentationMixin):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Journey
        fields = ("uuid", "status")
