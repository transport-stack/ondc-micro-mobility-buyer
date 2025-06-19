import json
import logging
from typing import Union

from ondc_micromobility_api.ondc_wrapper.base import APIClientBase
from ondc_micromobility_api.ondc_wrapper.fetch_fare_api import FetchFareAPI
from ondc_micromobility_api.ondc_wrapper.models.common import TicketRequestResponseAPI, ApiResponse


class TicketRequestAPI():
    SIGNATURE_KEY_NAME = "Signature"

    def __init__(
            self,
            token=None,
            tx_ref_no=None,
            txn_date=None,
            psp_specific_data=None,
            src_stn=None,
            dest_stn=None,
            grp_size=1,
    ):
        super().__init__(token)

        # Mandatory fields
        self.tx_ref_no = tx_ref_no
        self.txn_date = txn_date
        self.psp_specific_data = psp_specific_data
        self.src_stn = src_stn
        self.dest_stn = dest_stn
        self.no_of_tickets = grp_size
        self.grp_size = grp_size

    def post_api(self) -> Union[ApiResponse, None]:
        # Fetch the fare
        # TODO: Skip this step if the fare is already known
        fare_client = FetchFareAPI(
            token=self.token, Src_Stn=self.src_stn, Dest_Stn=self.dest_stn,
            Grp_Size=1
        )
        fare_response = fare_client.post_api()
        ticket_fare = fare_response.response["operator_Specific_Journeys"][0][
            "journey"
        ][0]["ticket_Fare"]

        # manually multiply the fare by the number of tickets
        # DMRC apis might not be working properly
        ticket_fare = ticket_fare * self.no_of_tickets

        # Create the QR Ticket Request
        qr_ticket_request = {
            "Requester_Id": self.REQUESTER_ID,
            "Language": 1,
            "TXN_Ref_No": self.tx_ref_no,
            "TXN_Date": self.txn_date,
            "PSP_Specific_Data": self.psp_specific_data,
            "Booking_Lat": "28.1111",
            "Booking_Lon": "77.222",
            "Mobile": "1234567899",  # Default value
            "TicketBlock": {
                "DynamicBlock": {
                    "Operators": [
                        {
                            "OpID": self.OPERATOR_ID_STR,
                            "NoofTickets": self.no_of_tickets,
                            "Validator_Info": "",
                            "TicketInfos": [
                                {
                                    "Grp_Size": f"{self.no_of_tickets}",
                                    "Src_Stn": self.src_stn,
                                    "Dest_Stn": self.dest_stn,
                                    "Activation_Date": self.current_datetime_formatted_str,
                                    "Ticket_Fare": ticket_fare,
                                    "Product_Id": 1,
                                    "Service_Id": 0,
                                    "Validity": 120,
                                    "Duration": 0,
                                }
                            ],
                        }
                    ]
                }
            },
        }

        signature = self.generate_signature(json.dumps(qr_ticket_request))
        details = {
            self.SIGNATURE_KEY_NAME: signature,
            "QR_Ticket_Request": qr_ticket_request,
        }

        payload = {"App_Ticket_Request": details}
        logging.debug(f"Payload: {payload}")

        response = self.post("Ticket_Request", payload)
        logging.debug(f"Response: {response}")
        return self.validate_response(response)

    def validate_response(self, data: dict) -> Union[ApiResponse, None]:
        try:
            # Check if the necessary keys are present
            assert "qR_Payload" in data
            assert "qrRecord" in data["qR_Payload"]
            assert "qR_Ticket_No" in data["qR_Payload"]["qrRecord"][0]
            assert "qR_Ticket_Block" in data["qR_Payload"]["qrRecord"][0]

            # Convert the dict to class objects
            response_obj = TicketRequestResponseAPI.from_dict(data)

            # Further validations based on your needs
            # Assuming "error_Text" exists at top level in your API response for ticket request
            assert data.get("error_Text") == ApiResponse.RESPONSE_SUCCESS_TEXT

            return response_obj

        except AssertionError:
            return None
