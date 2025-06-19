from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _

from modules.models import (
    DateTimeMixin,
    TransitMode,
    TransitModeMixin,
    TransactionStatus,
    TicketStatus,
    PaymentStatus,
)


@extend_schema_field(serializers.CharField)
class TicketPaymentStatusField(serializers.Field):
    def to_representation(self, value):
        if value is not None:
            return str(_(PaymentStatus(value).label))

    def to_internal_value(self, data):
        if data is not None:
            for mode in PaymentStatus.choices:
                if str(_(mode[1])) == data:
                    return mode[0]

        raise serializers.ValidationError("Invalid payment status")


@extend_schema_field(serializers.CharField)
class TicketStatusField(serializers.Field):
    def to_representation(self, value):
        if value is not None:
            return str(_(TicketStatus(value).label))

    def to_internal_value(self, data):
        if data is not None:
            for mode in TicketStatus.choices:
                if str(_(mode[1])) == data:
                    return mode[0]

        raise serializers.ValidationError("Invalid transit mode")


# TODO: check if it works
@extend_schema_field(serializers.CharField)
class TransactionStatusField(serializers.Field):
    def to_representation(self, value):
        if value is not None:
            return str(_(TransactionStatus(value).label))

    def to_internal_value(self, data):
        if data is not None:
            for mode in TransactionStatus.choices:
                if str(_(mode[1])) == data:
                    return mode[0]

        raise serializers.ValidationError("Invalid TransactionStatus")


@extend_schema_field(serializers.CharField)
class TransitModeField(serializers.Field):
    def to_representation(self, value):
        if value is not None:
            return TransitMode(value).name

    def to_internal_value(self, data):
        if data is not None:
            for mode in TransitMode:
                if mode.name == data:
                    return mode.value

        raise serializers.ValidationError("Invalid transit mode")


class DateTimeMixinSerializer(serializers.ModelSerializer):
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = DateTimeMixin
        fields = ["created_at", "updated_at"]


class TransitModeMixinSerializer(serializers.ModelSerializer):
    transit_mode = TransitModeField()

    class Meta:
        model = TransitModeMixin
        fields = ["transit_mode"]
