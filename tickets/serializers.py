from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from accounts.serializers import MyUserSerializer
from modules.serializers import (
    TransitModeMixinSerializer,
    TransactionStatusField,
    TicketStatusField,
    TicketPaymentStatusField,
)
from payments.models.transaction_setup import TransactionSerializer, TransactionSerializerV2
from tickets.models.fare_setup import FareBreakup
from tickets.models.ticket_recommendation_setup import TicketRecommendation
from tickets.models.ticket_setup import Ticket, TicketType, TicketUpdate
from transit.serializers import TransitOptionSerializer


class TicketTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketType
        fields = (
            "name",
            "discount_percentage",
            "is_description_required",
            "is_active",
            "description",
        )
        read_only_fields = fields


class FareBreakupSerializer(serializers.ModelSerializer):
    class Meta:
        model = FareBreakup
        exclude = ("id",)


class TicketSerializerMin(TransitModeMixinSerializer, MyUserSerializer):
    status = serializers.SerializerMethodField("get_ticket_status")
    payment_status = TicketPaymentStatusField()
    fare = serializers.SerializerMethodField("get_fare")
    transit_option = TransitOptionSerializer()

    @extend_schema_field(serializers.IntegerField)
    def get_ticket_status(self, obj):
        return obj.get_ticket_status().name

    @extend_schema_field(FareBreakupSerializer)
    def get_fare(self, obj):
        return FareBreakupSerializer(obj.fare).data

    class Meta:
        model = Ticket

        fields = [
            "transit_option",
            "pnr",
            "passenger_count",
            "fare",
            "journey_leg_index",
            "created_at",
            "amount",
            "status",
            "payment_status",
        ]

        read_only_fields = [
            "transit_option",
            "pnr",
            "passenger_count",
            "fare",
            "journey_leg_index",
            "created_at",
            "amount",
            "status",
        ]


class TicketSerializer(TransitModeMixinSerializer, MyUserSerializer):
    created_for = MyUserSerializer(read_only=True)
    ticket_type = serializers.SerializerMethodField("get_ticket_type")
    status = TicketStatusField()
    payment_status = TicketPaymentStatusField()
    fare = serializers.SerializerMethodField("get_fare")
    transit_option = TransitOptionSerializer()
    transaction = TransactionSerializerV2(many=True, read_only=True)

    @extend_schema_field(TicketTypeSerializer)
    def get_ticket_type(self, obj):
        return TicketTypeSerializer(obj.ticket_type).data

    @extend_schema_field(serializers.IntegerField)
    def get_ticket_status(self, obj):
        return obj.get_ticket_status().name

    @extend_schema_field(TicketTypeSerializer)
    def get_payment_status(self, obj):
        return TicketTypeSerializer(obj.ticket_type).data

    @extend_schema_field(FareBreakupSerializer)
    def get_fare(self, obj):
        return FareBreakupSerializer(obj.fare).data

    class Meta:
        model = Ticket

        fields = [
            "start_location_code",
            "start_location_name",
            "start_location_lat",
            "start_location_lng",
            "end_location_code",
            "end_location_name",
            "end_location_lat",
            "end_location_lng",
            "transit_option",
            "created_for",
            "pnr",
            "fare",
            "created_at",
            "updated_at",
            "status",
            "payment_status",
            "transit_pnr",
            "ticket_type",
            "transaction",
            "journey_leg_index",
            "passenger_count",
            "vehicle_number",
            "seat_no",
            "valid_till",
            "amount",
            "poc_name",
            "poc_phone",
            "ride_otp",
            "transaction_id",
            "service_details",
        ]

        read_only_fields = [
            "created_for",
            "pnr",
            "fare",
            "created_at",
            "updated_at",
            "status",
            "payment_status",
            "transit_pnr",
            "ticket_type",
            "journey_leg_index",
            "passenger_count",
            "seat_no",
            "valid_till",
            "amount",
            "poc_name",
            "poc_phone",
            "status",
            "start_location_lat",
            "start_location_lng",
            "end_location_lat",
            "end_location_lng",
            "service_details",
        ]


class TicketSerializerForInitiate(TicketSerializer):
    status = TicketStatusField()
    payment_status = TicketPaymentStatusField()

    def get_ticket_status(self, obj):
        return TicketSerializer.get_ticket_status(self, obj)

    class Meta:
        model = Ticket

        read_only_fields = ["status", "pnr", "payment_status"]
        fields = TicketSerializer.Meta.fields + [
            "start_location_lat",
            "start_location_lng",
            "end_location_lat",
            "end_location_lng",
        ]
        fields += read_only_fields


class TicketUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketUpdate
        fields = (
            "created_at",
            "details",
        )


class TicketCancellationSerializer(serializers.Serializer):
    cancellation_reason = serializers.CharField(
        required=False, default="Order cancelled by customer"
    )


class TicketRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = TicketRecommendation
        fields = ["start_location_code", "start_location_name", "end_location_code", "end_location_name", "transit_option", "weight"]
