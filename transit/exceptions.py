class ServiceNotAvailableException(Exception):
    """Exception raised when a service is not available for booking."""

    def __init__(self, message="The service is not available at this time."):
        self.message = message
        super().__init__(self.message)


class CalendarDateException(Exception):
    """Exception raised for issues related to CalendarDate."""
    def __init__(self, message="Service not available due to special scheduling today."):
        self.message = message
        super().__init__(self.message)
