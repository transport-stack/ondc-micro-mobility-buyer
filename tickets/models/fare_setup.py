from django.core.validators import MinValueValidator
from django.db import models

from accounts.models.user_setup import MyUser
from coupons.calculations import check_coupon_discount_from_fare
from modules.constants import round_school


# TODO: fare serializer returning null values


class FareBreakup(models.Model):
    basic = models.FloatField(
        default=0, validators=[MinValueValidator(0)], db_index=True
    )
    toll = models.FloatField(
        default=0, validators=[MinValueValidator(0)], db_index=True
    )
    convenience_charge = models.FloatField(
        default=0, validators=[MinValueValidator(0)], db_index=True
    )
    convenience_charge_tax = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Please enter calculated value.",
        db_index=True,
    )
    discount = models.FloatField(
        default=0, validators=[MinValueValidator(0)], db_index=True
    )
    add_on = models.FloatField(
        default=0, validators=[MinValueValidator(0)], db_index=True
    )
    add_on_tax = models.FloatField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Please enter calculated value.",
        db_index=True,
    )
    cancellation_chg = models.FloatField(
        default=0, validators=[MinValueValidator(0)], db_index=True
    )
    franchisee_service_charge = models.FloatField(
        default=0, validators=[MinValueValidator(0)], db_index=True
    )

    # stores total amount
    amount = models.FloatField(
        default=0.0, validators=[MinValueValidator(0)], db_index=True
    )

    coupon = models.ForeignKey(
        "coupons.Coupon", null=True, blank=True, on_delete=models.PROTECT
    )

    coupon_discount = models.FloatField(
        default=0.0, validators=[MinValueValidator(0)], db_index=True
    )
    quantity = models.IntegerField(default=1)

    def save(self, *args, **kwargs):
        self.calculate_and_update_amount()
        super(FareBreakup, self).save(*args, **kwargs)

    @property
    def tax(self):
        return self.convenience_charge_tax + self.add_on_tax

    def check_coupon(self, user: MyUser, coupon):
        self.coupon = coupon
        self.coupon_discount = check_coupon_discount_from_fare(user, coupon, self)
        self.calculate_and_update_amount()

    def apply_coupon(self, user: MyUser, coupon):
        self.unapply_all_coupons()
        self.coupon = coupon
        self.coupon_discount = check_coupon_discount_from_fare(user, coupon, self)
        self.save()

    def unapply_all_coupons(self):
        # TODO: maybe save fare amount here
        if self.coupon:
            self.coupon_discount = 0.0
            self.coupon = None
            self.save()

    def calculate_and_update_amount(self):
        self.amount = (
            self.quantity * self.basic
            + self.toll
            + self.convenience_charge
            + self.convenience_charge_tax
            + self.add_on
            + self.add_on_tax
            + self.franchisee_service_charge
            - self.cancellation_chg
            - self.coupon_discount
        )

        # self.amount = round_school(self.amount)

        if self.amount < 0:
            self.amount = 0

    @staticmethod
    def sum_of_objects(list_of_objects):
        booking_basic_fare = 0
        booking_toll_fare = 0
        booking_addon_val = 0
        booking_addon_tax_val = 0
        booking_franchisee_service_charge = 0
        booking_convenience_charge = 0
        booking_convenience_charge_tax = 0
        booking_discount = 0.0
        booking_cancellation_chg = 0.0

        for obj in list_of_objects:
            booking_basic_fare += obj.basic
            booking_toll_fare += obj.toll
            booking_addon_val += obj.add_on
            booking_addon_tax_val += obj.add_on_tax
            booking_franchisee_service_charge += obj.franchisee_service_charge
            booking_convenience_charge += obj.convenience_charge
            booking_convenience_charge_tax += obj.convenience_charge_tax
            booking_discount += obj.discount
            booking_cancellation_chg += obj.cancellation_chg

        final_obj = FareBreakup(
            basic=booking_basic_fare,
            toll=booking_toll_fare,
            convenience_charge=booking_convenience_charge,
            convenience_charge_tax=booking_convenience_charge_tax,
            franchisee_service_charge=booking_franchisee_service_charge,
            discount=booking_discount,
            add_on=booking_addon_val,
            add_on_tax=booking_addon_tax_val,
            cancellation_chg=booking_cancellation_chg,
        )
        final_obj.calculate_and_update_amount()
        return final_obj
