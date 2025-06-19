import logging

from tickets.models.ticket_setup import TicketType

logger = logging.getLogger(__name__)


def create_ticket_type(ticket_type_data):
    ticket_type, created = TicketType.objects.update_or_create(
        pk=ticket_type_data["pk"], defaults=ticket_type_data
    )

    action = "created" if created else "updated"
    logger.info(f"TicketType {ticket_type_data['name']} {action}")


def setup_ticket_types():
    logger.info("Adding ticket types")
    ticket_types = [
        {"pk": 1, "name": "General", "is_active": True},
        # {"pk": 2, "name": "Child", "is_active": True},
        # {"pk": 3, "name": "Differently Abled", "is_active": True},
        # {"pk": 4, "name": "Senior Citizen", "is_active": True},
        # {"pk": 5, "name": "Non Binary", "is_active": True},
        # {"pk": 6, "name": "Police", "is_active": True},
        # {"pk": 7, "name": "Attendant", "is_active": True},
        # {"pk": 8, "name": "Specially Able 50%", "is_active": True},
        # {"pk": 9, "name": "Specially Able 100%", "is_active": True},
        # {"pk": 10, "name": "Student", "is_active": True},
        {"pk": 2, "name": "Pink", "is_active": True},
    ]

    for ticket_type_data in ticket_types:
        create_ticket_type(ticket_type_data)
