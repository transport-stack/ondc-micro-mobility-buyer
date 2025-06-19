from django.apps import AppConfig


class TicketsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tickets"

    def ready(self):
        from tickets.models.signals import create_ticket
        from tickets.models.signals import update_ticket_status
        from tickets.models.signals import update_ticket_amount

