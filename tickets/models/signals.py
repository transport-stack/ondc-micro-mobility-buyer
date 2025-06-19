import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from modules.constants import NAMMAYATRI_ENUM, INTEGRATED_TICKETING_ENUM
from modules.models import TicketStatus, TransitMode, PaymentStatus
from nammayatri.serializers import OrderUpdateSerializer, CaptainDetailsSerializer
from ondc_micromobility_api.constants import NammayatriCancellationReasons
from tickets.models.fare_setup import FareBreakup
from tickets.models.ticket_setup import TicketUpdate, Ticket
from transit.utils import NammayatriNotification, TransitState, DMRCNotification, NammayatriState, NammayatriTransitMessages

IN_STD_CODE = "+91"

"""
add post save signal on ticket model for new object only
"""


@receiver(post_save, sender=Ticket)
def create_ticket(sender, instance, created, **kwargs):
    # check if ticket is created
    if created:
        # send fcm
        try:
            if instance.is_status_confirmed():
                notification = DMRCNotification(instance, TransitState.CONFIRMED)
                notification_title = notification.get_title()
                notification_message = notification.get_message()
                instance.send_user_status_notification(notification_title, notification_message, notification)
        except Exception as e:
            logging.exception(e)
        TicketUpdate.objects.create(ticket=instance, trigger_signal=False, details={"status": "created"})


# TODO: Use this to refactor following code
# https://chat.openai.com/share/aa86dda8-7e54-4887-adb8-37e66648eea6
@receiver(post_save, sender=TicketUpdate)
def update_ticket_status(sender, instance, created, **kwargs):
    if not instance.trigger_signal:
        return
    other_updates = {}
    if created:  # Check if the instance is being created
        # Call the process_update function of the related TransitOption instance
        if instance.ticket:
            # Logic to process the update
            # This will vary according to different transit_option
            ticket = instance.ticket
            transit_pnr = ticket.transit_pnr
            transit_option = ticket.transit_option

            if not transit_option:
                logging.error(f"Transit option not found for ticket: {ticket}")
                return
            transit_mode = transit_option.transit_mode
            transit_provider = transit_option.provider.name

            if not (transit_mode and transit_provider):
                logging.error(
                    f"Transit mode or provider not found for ticket: {ticket}"
                )
                return

            update_ticket_status_bool = False
            service_details = None
            _new_status = TicketStatus.PENDING
            notification = None
            notification_title = None
            notification_message = None
            if ticket.is_transit_provider(NAMMAYATRI_ENUM, INTEGRATED_TICKETING_ENUM):
                # do something
                response_data = instance.details
                service_details = response_data
                if response_data:
                    # make sure response has two fields, orderId and status
                    OrderUpdateSerializer(data=response_data).is_valid(
                        raise_exception=True
                    )

                    status_value = response_data["status"]
                    """
                    Rapido Status	Ticket Status should be converted to
                    accepted	CONFIRMED
                    arrived	No Impact
                    rider_cancelled	CANCELLED
                    customer_cancelled	CANCELLED
                    started CONFIRMED ( in case accepted didn't come)
                    dropped	EXPIRED
                    aborted	CANCELLED
                    expired	CANCELLED
                    """
                    if status_value == "accepted":  # or status_value == 'arrived':
                        """{
                          "orderId": "9e93e3c7-98e5-4155-bfa8-1738c999f270",
                          "status": "accepted",
                          "metadata": {
                              "referenceId": "1234343"
                          },
                          "eta": 6,
                          "captainDetails": {
                              "name": "Harry Potter",
                              "currentVehicle": {
                                  "number": "ADSDSD"
                              },
                              "mobile": "1234567890"
                          },
                           "otp": "2121",
                           "trackURL": "https://trk.staging.plectrum.dev/track/ad32914894db55f6afaf8799"
                        }
                        """
                        eta = response_data["eta"]
                        if eta is None:
                            raise Exception("ETA is None")

                        captain_data = response_data["captainDetails"]
                        captain_serializer = CaptainDetailsSerializer(data=captain_data)
                        if captain_serializer.is_valid():
                            poc_name = captain_data.get("name") or "Your Captain"
                            poc_name = poc_name.title()
                            other_updates = {
                                "poc_name": poc_name,
                                "poc_phone": IN_STD_CODE + captain_data["mobile"][-10:],
                                "vehicle_number": captain_data["currentVehicle"][
                                    "number"
                                ],
                            }

                            vehicle_number = captain_data["currentVehicle"][
                                "number"
                            ]

                            update_ticket_status_bool = True
                            _new_status = TicketStatus.CONFIRMED

                            # fcm
                            notification = NammayatriNotification(ticket, NammayatriState.ACCEPTED)
                            notification_title = notification.get_title()
                            notification_message = notification.get_message(name=poc_name,
                                                                            vehicle_number=vehicle_number)
                        else:
                            raise captain_serializer.errors

                    elif status_value == "customer_cancelled":
                        update_ticket_status_bool = True
                        _new_status = TicketStatus.CANCELLED

                        # no fcm
                    elif status_value == "started":
                        update_ticket_status_bool = True
                        _new_status = TicketStatus.CONFIRMED

                        notification = NammayatriNotification(ticket, NammayatriState.STARTED)
                        notification_title = notification.get_title()
                        notification_message = notification.get_message()

                    elif status_value == "dropped":
                        if "amount" not in response_data:
                            # if fraud case, no amount will be there
                            """
                            {
                                "orderId": "9e93e3c7-98e5-4155-bfa8-1738c999f270",
                                "status": "dropped",
                                "metadata": {
                                    "referenceId": "1234343"
                                },
                                "location": {
                                    "lat": 12.98766,
                                    "lng": 77.5921071
                                },
                                "distanceTravelled": 9.76,
                                "travelDuration": 25.65,
                                "dropTime": 1583122957031
                            }
                            """
                            update_ticket_status_bool = True
                            # else update the status to CANCELLED, user should not pay for this case
                            _new_status = TicketStatus.CANCELLED
                            notification = NammayatriNotification(ticket, NammayatriState.CANCELLED)
                            notification_title = notification.get_title()
                            notification_message = notification.get_message()

                        else:
                            """
                            {
                                "orderId": "9e93e3c7-98e5-4155-bfa8-1738c999f270",
                                "status": "dropped",
                                "metadata": {
                                    "referenceId": "1234343"
                                },
                                "location": {
                                    "lat": 12.98766,
                                    "lng": 77.5921071
                                },
                                "amount": 75,
                                "distanceTravelled": 9.76,
                                "travelDuration": 25.65,
                                "dropTime": 1583122957031
                            }
                            """
                            # we are updating ticket's amount twice
                            # once in ticket.update_fare and then at the end on update_status
                            # TODO: optimize this
                            amount = float(response_data["amount"])
                            ticket.update_fare(amount)
                            other_updates = {
                                "amount": amount,
                            }

                            update_ticket_status_bool = True
                            # if previous status of ticket was CONFIRMED, then only update status to EXPIRED
                            # else update the status to CANCELLED
                            if ticket.status == TicketStatus.CONFIRMED:
                                _new_status = TicketStatus.EXPIRED

                                # if ticket is of rapido + auto rickshaw, then convert payment status to PAID
                                if (ticket.transit_option.transit_mode == TransitMode.AUTO_RICKSHAW and
                                        transit_option.provider.name in {NAMMAYATRI_ENUM, INTEGRATED_TICKETING_ENUM}):
                                    other_updates["payment_status"] = PaymentStatus.COMPLETED

                                    # Notification #1
                                    # if the mode is auto + rapido, send fcm
                                    ticket.send_user_status_notification(
                                        title=NammayatriTransitMessages.PAY_DIRECTLY_TO_DRIVER["title"],
                                        message=NammayatriTransitMessages.PAY_DIRECTLY_TO_DRIVER["message"])

                                # Notification #2
                                notification = NammayatriNotification(ticket, NammayatriState.DROPPED)
                                notification_title = notification.get_title()
                                notification_message = notification.get_message()
                            else:
                                _new_status = TicketStatus.CANCELLED
                                notification = NammayatriNotification(ticket, NammayatriState.CANCELLED)
                                notification_title = notification.get_title()
                                notification_message = notification.get_message()

                    elif status_value == "aborted":
                        update_ticket_status_bool = True
                        _new_status = TicketStatus.CANCELLED

                        notification = NammayatriNotification(ticket, NammayatriState.CANCELLED)
                        notification_title = notification.get_title()
                        notification_message = notification.get_message()
                    elif status_value == "expired":
                        update_ticket_status_bool = True
                        if ticket.status == TicketStatus.CONFIRMED:
                            _new_status = TicketStatus.EXPIRED
                            notification = NammayatriNotification(ticket, NammayatriState.DROPPED)
                            notification_title = notification.get_title()
                            notification_message = notification.get_message()
                        else:
                            _new_status = TicketStatus.CANCELLED
                            notification = NammayatriNotification(ticket, NammayatriState.CANCELLED)
                            notification_title = notification.get_title()
                            notification_message = notification.get_message()

                    elif status_value == "arrived":
                        update_ticket_status_bool = True
                        _new_status = TicketStatus.CONFIRMED

                        notification = NammayatriNotification(ticket, NammayatriState.ARRIVED)
                        notification_title = notification.get_title()
                        notification_message = notification.get_message(name=ticket.poc_name,
                                                                        vehicle_number=ticket.vehicle_number,
                                                                        pin=ticket.created_for.pin)
                        """
                        {
                          "orderId": "9e93e3c7-98e5-4155-bfa8-1738c999f270",
                          "status": "arrived",
                          "metadata": {
                              "referenceId": "1234343"
                          },
                          "captainDetails": {
                              "name": "Harry Potter",
                              "currentVehicle": {
                                  "number": "ADSDSD"
                              },
                              "mobile": "1234567890"
                          },
                           "otp": "2121",
                           "trackURL": "https://trk.staging.plectrum.dev/track/ad32914894db55f6afaf8799"
                        }
                        """

            # update ticket status
            if update_ticket_status_bool:
                ticket.update_status(
                    _new_status,
                    service_details=service_details,
                    other_updates=other_updates,
                    notification_title=notification_title,
                    notification_message=notification_message,
                    notification=notification
                )

            logging.info(f"ticket updates called")
        else:
            logging.error(f"TransitOption not found for ticket: {instance.ticket}")

@receiver(post_save, sender=FareBreakup)
def update_ticket_amount(sender, instance, created, **kwargs):
    logging.info(f"update_ticket_amount called")
    fare_obj = instance
    ticket_obj = Ticket.objects.filter(fare=fare_obj).first()
    if ticket_obj and ticket_obj.amount != fare_obj.amount:
        ticket_obj.amount = fare_obj.amount
        ticket_obj.save()
