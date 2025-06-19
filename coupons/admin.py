from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from coupons.models import Coupon


# Register your models here.

class CouponAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ('is_visible', 'code', 'name', 'description', 'max_discount_amount', 'max_discount_percent')


admin.site.register(Coupon, CouponAdmin)
