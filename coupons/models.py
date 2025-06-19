from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from modules.models import DateTimeMixin, ActiveMixin
from common.constants import alphanumeric_regex


class Coupon(DateTimeMixin, ActiveMixin):
    is_visible = models.BooleanField(default=True, db_index=True)
    code = models.CharField(
        max_length=16, primary_key=True, validators=[alphanumeric_regex]
    )
    name = models.CharField(max_length=32, null=True, blank=True)
    description = models.CharField(max_length=128, null=False, blank=False)
    valid_from = models.DateTimeField(null=False, blank=False, db_index=True)
    valid_till = models.DateTimeField(null=True, blank=True, db_index=True)
    max_discount_amount = models.FloatField(
        validators=[MinValueValidator(0)], null=False, blank=False
    )
    max_discount_percent = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=False,
        blank=False,
    )

    class Meta:
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"
        ordering = ("-created_at",)

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        if self.name is None:
            self.name = self.code
        super(Coupon, self).save(*args, **kwargs)
