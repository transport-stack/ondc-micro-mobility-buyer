from typing import Dict
from typing import List, Union, Type
from typing import Optional


class Station:
    def __init__(self, station_ID: int, station_Name: str, station_Location: str):
        self.station_ID = station_ID
        self.station_Name = station_Name
        self.station_Location = station_Location

    @classmethod
    def from_dict(cls, data: dict) -> "Station":
        return cls(
            station_ID=data["station_ID"],
            station_Name=data["station_Name"],
            station_Location=data["station_Location"],
        )


class RouteResponse:
    def __init__(
            self,
            error_Code: int,
            error_Text: str,
            operator_Id: int,
            operator_Type: int,
            product_Id: str,
            validity: str,
            duration: str,
            noOfRoutes: Optional[int],
            noOfStations: int,
            route_Details: List,
            station_Details: List[List[Station]],
    ):
        self.error_Code = error_Code
        self.error_Text = error_Text
        self.operator_Id = operator_Id
        self.operator_Type = operator_Type
        self.product_Id = product_Id
        self.validity = validity
        self.duration = duration
        self.noOfRoutes = noOfRoutes
        self.noOfStations = noOfStations
        self.route_Details = route_Details
        self.station_Details = station_Details

    @classmethod
    def from_dict(cls, data: dict) -> "RouteResponse":
        station_details = [
            [Station.from_dict(station) for station in station_group["station"]]
            for station_group in data["station_Details"]
        ]
        return cls(
            error_Code=data["error_Code"],
            error_Text=data["error_Text"],
            operator_Id=data["operator_Id"],
            operator_Type=data["operator_Type"],
            product_Id=data["product_Id"],
            validity=data["validity"],
            duration=data["duration"],
            noOfRoutes=data["noOfRoutes"],
            noOfStations=data["noOfStations"],
            route_Details=data["route_Details"],
            station_Details=station_details,
        )


class ApiResponse:
    RESPONSE_SUCCESS_TEXT = "Success"

    def __init__(self, signature: str = None):
        self.response = None
        self.signature = signature

    @classmethod
    def from_dict(cls: Type["ApiResponse"], data: dict) -> Union["ApiResponse", None]:
        raise NotImplementedError(
            "from_dict method should be implemented in child class."
        )

    def is_success(self) -> bool:
        """
        Check if the API response is successful.

        Returns:
            bool: True if successful, False otherwise.
        """
        raise NotImplementedError(
            "is_success method should be implemented in child class."
        )


class RouteResponseAPI(ApiResponse):
    def __init__(
            self, route_Response: List[RouteResponse], route_Response_Signature: str
    ):
        super().__init__(route_Response_Signature)
        self.response = route_Response
        self.route_Response = route_Response

    @classmethod
    def from_dict(cls, data: dict) -> "RouteResponseAPI":
        route_responses = [
            RouteResponse.from_dict(item) for item in data["route_Response"]
        ]
        return cls(
            route_Response=route_responses,
            route_Response_Signature=data["route_Response_Signature"],
        )

    def is_success(self) -> bool:
        return self.route_Response[0].error_Text == self.RESPONSE_SUCCESS_TEXT

    def get_station_details(self) -> List[List[Station]]:
        return self.route_Response[0].station_Details


class FareResponseAPI(ApiResponse):
    """
    fare in paise: self.fetch_Fare_Response["operator_Specific_Journeys"][0]["journey"][0]["ticket_Fare"]
    """

    def __init__(self, fetch_Fare_Response: dict, fetch_Fare_Signature: str):
        super().__init__(fetch_Fare_Signature)
        self.response = fetch_Fare_Response
        self.fetch_Fare_Response = fetch_Fare_Response

    @classmethod
    def from_dict(cls, data: dict) -> "FareResponseAPI":
        return cls(
            fetch_Fare_Response=data["fetch_Fare_Response"],
            fetch_Fare_Signature=data["fetch_Fare_Signature"],
        )

    def is_success(self) -> bool:
        return self.fetch_Fare_Response["error_Text"] == self.RESPONSE_SUCCESS_TEXT

    def get_fare(self) -> float:
        return self.fetch_Fare_Response["operator_Specific_Journeys"][0]["journey"][0]["ticket_Fare"]

    def get_fare_inr(self) -> float:
        return self.get_fare() / 100.0


class TicketRequestResponseAPI(ApiResponse):
    def __init__(self, qR_Payload: Dict[str, List[Dict[str, str]]], qR_Signature: str):
        super().__init__(qR_Signature)
        self.response = qR_Payload
        self.qR_Payload = qR_Payload

    @classmethod
    def from_dict(cls, data: dict) -> "TicketRequestResponseAPI":
        return cls(
            qR_Payload=data["qR_Payload"],
            qR_Signature=data["qR_Signature"],
        )

    def is_success(self) -> bool:
        return self.qR_Payload.get("error_Text", "") == self.RESPONSE_SUCCESS_TEXT

    def get_qr_ticket_numbers(self) -> List[str]:
        return [
            record.get("qR_Ticket_No") for record in self.qR_Payload.get("qrRecord", [])
        ]

    def get_qr_ticket_block(self) -> List[str]:
        return [
            record.get("qR_Ticket_Block")
            for record in self.qR_Payload.get("qrRecord", [])
        ]

    def get_qr_ticket_blocks(self) -> List[str]:
        return [
            record.get("qR_Ticket_Block")
            for record in self.qR_Payload.get("qrRecord", [])
        ]


class FareFromSourceToAllDestinationsResponseAPI(ApiResponse):
    """
    Extract fare data from objSourecToDestination in the response.
    Example: self.objSourecToDestination[0]['fare']
    """

    def __init__(self, objSourecToDestination: list):
        super().__init__()
        self.objSourecToDestination = objSourecToDestination

    @classmethod
    def from_dict(cls, data: dict) -> "FareFromSourceToAllDestinationsResponseAPI":
        return cls(objSourecToDestination=data["objSourecToDestination"])

    def is_success(self) -> bool:
        # Assuming success is determined by the presence of data in objSourecToDestination.
        return bool(self.objSourecToDestination)

    def get_fare_matix(self):
        ""
