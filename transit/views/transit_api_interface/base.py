from modules.models import TransitMode


def validate_transit_mode(transit_mode):
    if transit_mode not in TransitMode.values:
        raise ValueError("Invalid transit mode")


class TransitAPI:
    def __init__(self):
        self.message = None
        self.transit_pnr = None
        pass

    def estimate(self, transit_mode, pickup_location, drop_location, **kwargs):
        validate_transit_mode(transit_mode)

        # Here we call the actual implementation.
        return self._estimate(transit_mode, pickup_location, drop_location, **kwargs)

    def _estimate(self, transit_mode, pickup_location, drop_location, **kwargs):
        # This should be overridden by subclasses
        raise NotImplementedError

    def book(self, user, transit_mode, pickup_location, drop_location, **kwargs):
        validate_transit_mode(transit_mode)

        # Here we call the actual implementation.
        return self._book(user, transit_mode, pickup_location, drop_location, **kwargs)

    def _book(self, user, transit_mode, pickup_location, drop_location, **kwargs):
        raise NotImplementedError

    def cancel(self, transit_pnr, cancellation_reason):
        return self._cancel(transit_pnr, cancellation_reason)

    def _cancel(self, transit_pnr, cancellation_reason):
        raise NotImplementedError
# TODO Work on this
    # def is_eligible(self, user, transit_mode, pickup_location, drop_location):
    #     return self._is_eligible(user, transit_mode, pickup_location, drop_location)

    # def _is_eligible(self, user, transit_mode, pickup_location, drop_location):
    #     raise NotImplementedError
    def is_eligible(self, transit_mode, pickup_location, drop_location):
        return self._is_eligible(transit_mode, pickup_location, drop_location)

    def _is_eligible(self,transit_mode, pickup_location, drop_location):
        raise NotImplementedError
