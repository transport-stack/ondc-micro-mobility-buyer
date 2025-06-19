from abc import ABC, abstractmethod
from enum import Enum


class TransitState(Enum):
    CONFIRMED = "Confirmed"
    PENDING = "Pending"
    CANCELLED = "Cancelled"
    EXPIRED = "Expired"


class NammayatriState(Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    ARRIVED = "ARRIVED"
    STARTED = "STARTED"
    DROPPED = "DROPPED"
    CANCELLED = "CANCELLED"


# Example Enum for DMRC States
class DMRCState(Enum):
    CONFIRMED = "CONFIRMED"


class NotificationStrategy(ABC):

    def __init__(self, ticket, transit_state):
        self.ticket = ticket
        self.transit_state = transit_state

    @abstractmethod
    def get_title(self) -> str:
        pass

    @abstractmethod
    def get_message(self, **kwargs) -> str:
        pass

    def get_extra_params(self) -> dict:
        """Create and return the extra_params dictionary."""
        params = {
            "transit_state": self.transit_state.value,
            "type": "ptx_ticket_status"
        }

        return params


class TransitMessagesBase(ABC):

    @classmethod
    def get_title(cls, state_enum, transit_state):
        return cls._find_status(transit_state.value).get("title", "")

    @classmethod
    def get_message(cls, state_enum, transit_state, **kwargs):
        # kwargs.setdefault('name', 'Driver')  # Default name if not provided in kwargs
        status_dict = cls._find_status(transit_state.value)
        if "message_template" in status_dict:
            return status_dict["message_template"].format(**kwargs)
        return status_dict.get("message", "")

    @classmethod
    def _find_status(cls, state: str):
        status = getattr(cls, state, None)
        if status is None:
            raise ValueError(f"Invalid state: {state}")
        return status


class NammayatriTransitMessages(TransitMessagesBase):
    PENDING = {
        "title": "Looking for ride",
        "message": "Looking for a ride around you."
    }

    ACCEPTED = {
        "title": "Ride accepted",
        "message_template": "{name} ({vehicle_number}) is on the way."
    }

    ARRIVED = {
        "title": "Ride arrived",
        "message_template": "{name} ({vehicle_number}) is here. Share pin: {pin} with the driver."
    }

    STARTED = {
        "title": "Ride started",
        "message": "Your ride has started. Enjoy your ride."
    }

    DROPPED = {
        "title": "Ride completed",
        "message": "Your ride has completed. Please make payment for your previous journey for using it again."
    }

    CANCELLED = {
        "title": "Ride cancelled",
        "message": "Your ride was cancelled. Please try again."
    }
    PAY_DIRECTLY_TO_DRIVER = {
        "title": "Pay directly to your captain",
        "message": "Pay directly to your captain after the ride via cash or UPI."
    }


class DMRCTransitMessages(TransitMessagesBase):
    CONFIRMED = {
        "title": "Ticket confirmed",
        "message": "Please scan the QR code at the gate."
    }


class NammayatriNotification(NotificationStrategy):
    messages_class = NammayatriTransitMessages  # Directly referencing the message class

    def get_title(self) -> str:
        return self.messages_class.get_title(NammayatriState, self.transit_state)

    def get_message(self, **kwargs) -> str:
        return self.messages_class.get_message(NammayatriState, self.transit_state, **kwargs)


class DMRCNotification(NotificationStrategy):
    messages_class = DMRCTransitMessages  # Directly referencing the message class

    def get_title(self) -> str:
        return self.messages_class.get_title(DMRCState, self.transit_state)

    def get_message(self, **kwargs) -> str:
        return self.messages_class.get_message(DMRCState, self.transit_state, **kwargs)


if __name__ == "__main__":
    # Just a mockup ticket for demonstration purposes.
    ticket = type("Ticket", (object,),
                  {"send_notification": lambda self, title, msg: print(f"Sent: {title} - {msg}")})()

    # Create a notification object for Rapido when the state is "ACCEPTED"
    notification = NammayatriNotification(ticket, NammayatriState.ACCEPTED)
    title = notification.get_title()
    message = notification.get_message(name="Ravinder", vehicle_number="DL01L1234")
    ticket.send_notification(title, message)

    # DMRC Test
    notification = DMRCNotification(ticket, DMRCState.CONFIRMED)
    title = notification.get_title()
    message = notification.get_message()
    ticket.send_notification(title, message)
