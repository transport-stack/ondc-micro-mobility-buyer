from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilterBuilder

from .models.payment_gateway_setup import PaymentGateway, PaymentMode
from .models.transaction_setup import PaymentGatewayMode, Transaction
from import_export.admin import ImportExportModelAdmin

class TransactionAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = (
        "pk",
        "link_to_user",
        "amount",
        "gateway_transaction_status",
        "status",
        "transaction_type",
        "created_at",
    )
    search_fields = (
        "pk",
        "user__username",
        "status",
        "gateway_transaction_status",
    )
    list_filter = (
        "status",
        "gateway_transaction_status",
        "transaction_type",
        ("created_at", DateRangeFilterBuilder()),
    )
    readonly_fields = ("created_at", "updated_at", "user", "original_transaction", "gateway_order_id", "gateway_transaction_id", "transaction_type", "gateway_mode")

    def link_to_user(self, obj):
        if obj.user is None:
            return "-"

        link = reverse(
            "admin:%s_%s_change"
            % (obj.user._meta.app_label, obj.user._meta.model_name),
            args=[obj.user.id],
        )
        return format_html('<a target="_blank" href="{}">{}</a>', link, obj.user)

    link_to_user.short_description = "User"


admin.site.register(Transaction, TransactionAdmin)
admin.site.register(PaymentMode)
admin.site.register(PaymentGateway)
admin.site.register(PaymentGatewayMode)
