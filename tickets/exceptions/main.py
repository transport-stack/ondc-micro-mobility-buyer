class TicketError(Exception):
    """Base exception for all ticket related errors"""

    pass


class TransactionAlreadyExistsError(TicketError):
    def __init__(self):
        super().__init__(
            "Already has a ticket transaction. Cannot create another transaction"
        )


class PostpaidTicketStatusPendingCannotCreateTransactionError(TicketError):
    def __init__(self):
        super().__init__(
            "Cannot create transaction for postpaid ticket in pending state"
        )


class MissingTransactionError(TicketError):
    """Raised when trying to confirm a ticket without a transaction"""

    def __init__(self):
        super().__init__("No transaction found")


class TransactionNotSuccessfulError(TicketError):
    """Raised when trying to confirm a ticket with an unsuccessful transaction"""

    def __init__(self):
        super().__init__("Unsuccessful transaction")


class PaymentAmountMismatchError(TicketError):
    """Raised when the payment amount does not match the ticket amount"""

    def __init__(self):
        super().__init__("Different transaction/ticket amount")


class InvalidStatusUpdateError(TicketError):
    """Raised when trying to perform an invalid status update"""

    def __init__(self, current_status, new_status):
        super().__init__(
            f"Invalid status update request from {current_status} -> {new_status}"
        )


class MissingFareError(TicketError):
    """Raised when trying to create a ticket without a fare"""

    def __init__(self):
        super().__init__("Fare is required to create a ticket")
