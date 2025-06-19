from django.apps import apps

from accounts.models.user_setup import MyUser
from coupons.models import Coupon
from modules.models import TicketStatus, PaymentType


class CouponCodes:
    FIRSTFREE = "FIRSTFREE"


def get_coupon_from_code(code: str) -> (bool, Coupon):
    if code is None:
        return False, Coupon.objects.none()
    coupons = Coupon.objects.filter(code=code)
    if coupons.exists():
        return True, coupons.first()
    else:
        return False, coupons.none()


def is_coupon_valid_for_user(user: MyUser, coupon: Coupon) -> bool:
    TicketModel = apps.get_model("tickets", "Ticket")
    if coupon.active:
        if coupon.code == CouponCodes.FIRSTFREE:
            # is this user new user
            tickets_count = TicketModel.objects.filter(
                created_by=user,
                payment_type__in=(PaymentType.PREPAID, PaymentType.POSTPAID),
                status__in=(TicketStatus.CONFIRMED, TicketStatus.EXPIRED),
            ).count()
            if tickets_count == 0:
                return True
        else:
            # return True for all others coupons
            return True
    return False


# generic discount function
def get_total_discount_amount(fare, coupon: Coupon) -> float:
    percent_discount_amount = round(
        fare.amount * (coupon.max_discount_percent / 100), 0
    )
    return min(percent_discount_amount, coupon.max_discount_amount)


def check_coupon_discount_from_fare(user: MyUser, coupon: Coupon, fare) -> float:
    if is_coupon_valid_for_user(user, coupon):
        return get_total_discount_amount(fare, coupon)
    else:
        raise NotImplementedError("Coupon not valid for user/ticket")
