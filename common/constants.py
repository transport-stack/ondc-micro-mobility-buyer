from django.core.validators import RegexValidator
from rest_framework import serializers

alphanumeric_regex = RegexValidator(
    r"^[0-9a-zA-Z]*$", "Only alphanumeric characters are allowed."
)
upper_alphanumeric_underscore_regex = RegexValidator(
    r"^[0-9A-Z_]*$",
    "Only uppercase alphanumeric characters with underscore are allowed.",
)


class NoneSerializer(serializers.Serializer):
    pass
