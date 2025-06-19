import django_filters

from tickets.models.ticket_setup import Ticket


class TicketFilter(django_filters.FilterSet):
    valid_till = django_filters.DateFilter(
        field_name="valid_till", lookup_expr="lte", required=False, label="Valid Till"
    )

    class Meta:
        model = Ticket
        fields = ["valid_till"]
