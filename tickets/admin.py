from django.urls import reverse
# Register your models here.
from django.contrib.admin import ModelAdmin
from django.urls import reverse
from django.utils.html import format_html
from rangefilter.filters import (
    DateRangeFilterBuilder,
)

from modules.models import PaymentStatus, TicketStatus
from tickets.models import TicketRecommendation
from tickets.models.ticket_setup import Ticket, TicketType, TicketUpdate, FareBreakup
from import_export.admin import ImportExportModelAdmin

from django.contrib import admin
from django.contrib import messages


class TicketUpdateAdmin(ImportExportModelAdmin, ModelAdmin):
    # show created_at and updated_at fields
    readonly_fields = ("created_at", "updated_at")
    # add search fields
    search_fields = (
        "ticket__pnr",
        "ticket__transit_pnr",
        "ticket__created_for__username",
    )
    # add filter fields, with date
    list_filter = (
        "ticket__transit_option__provider",
        "ticket__transit_option__transit_mode",
        ("created_at", DateRangeFilterBuilder()),
    )
    # add list display fields
    list_display = (
        "ticket",
        "created_at",
        "details",
    )

    autocomplete_fields = (
        "ticket",
    )  # Add this line to enable autocomplete for the ticket field


def mark_payment_completed(modeladmin, request, queryset):
    updated_count = queryset.update(
        payment_status=PaymentStatus.COMPLETED)  # Replace with the correct value for completed status
    messages.success(request, f'{updated_count} ticket(s) marked as payment completed.')


mark_payment_completed.short_description = "Mark selected tickets as payment completed"


def mark_payment_incomplete(modeladmin, request, queryset):
    updated_count = queryset.update(
        payment_status=PaymentStatus.NOT_COMPLETED)  # Replace with the correct value for completed status
    messages.success(request, f'{updated_count} ticket(s) marked as payment incomplete.')


mark_payment_incomplete.short_description = "Mark selected tickets as payment incomplete"


def mark_status_confirmed(modeladmin, request, queryset):
    updated_count = queryset.update(status=TicketStatus.CONFIRMED)
    messages.success(request, f'{updated_count} ticket(s) marked as Confirmed.')


mark_status_confirmed.short_description = "Mark selected tickets as Confirmed"


def mark_status_pending(modeladmin, request, queryset):
    updated_count = queryset.update(status=TicketStatus.PENDING)
    messages.success(request, f'{updated_count} ticket(s) marked as Pending.')


mark_status_pending.short_description = "Mark selected tickets as Pending"


def mark_status_cancelled(modeladmin, request, queryset):
    updated_count = queryset.update(status=TicketStatus.CANCELLED)
    messages.success(request, f'{updated_count} ticket(s) marked as Cancelled.')


mark_status_cancelled.short_description = "Mark selected tickets as Cancelled"


def mark_status_expired(modeladmin, request, queryset):
    updated_count = queryset.update(status=TicketStatus.EXPIRED)
    messages.success(request, f'{updated_count} ticket(s) marked as Expired.')


mark_status_expired.short_description = "Mark selected tickets as Expired"


class TicketAdmin(ImportExportModelAdmin, ModelAdmin):
    autocomplete_fields = ["transaction"]  # Add this line
    readonly_fields = (
        "created_at", "updated_at", "created_by", "created_for",
        "start_location_name", "end_location_name",
        "pnr", "transit_option", "journey_leg_index",
        "ticket_type", "fare"

    )
    search_fields = ("pnr", "transit_pnr", "created_for__username")
    list_display = (
        "pnr",
        "ticket_updates",
        "created_at",
        "link_to_created_for",
        "start_location_name",
        "end_location_name",
        "status",
        "amount",
        "payment_status",
        "transit_pnr",
        "transit_option",
        "start_location_name",
        "end_location_name",
    )
    list_filter = (
        "status",
        "payment_status",
        ("created_at", DateRangeFilterBuilder()),
    )  # Add this line
    actions = [mark_payment_completed,
               mark_payment_incomplete,
               mark_status_confirmed,
               mark_status_pending,
               mark_status_cancelled,
               mark_status_expired]

    def ticket_updates(self, obj):
        url = reverse("admin:tickets_ticketupdate_changelist")
        return format_html('<a target="blank" href="{}?ticket__pnr__exact={}">View Updates</a>', url, obj.pnr)

    ticket_updates.short_description = "Ticket Updates"

    def ticket_updates(self, obj):
        url = reverse("admin:tickets_ticketupdate_changelist")
        return format_html('<a target="blank" href="{}?ticket__pnr__exact={}">View Updates</a>', url, obj.pnr)

    ticket_updates.short_description = "Ticket Updates"

    def link_to_created_for(self, obj):
        if obj.created_for is None:
            return "-"
        link = reverse(
            "admin:%s_%s_change"
            % (obj.created_for._meta.app_label, obj.created_for._meta.model_name),
            args=[obj.created_for.id],
        )
        return format_html('<a href="{}">{}</a>', link, obj.created_for)

    link_to_created_for.short_description = "Created For"


class TicketTypeAdmin(ImportExportModelAdmin, ModelAdmin):
    list_display = [field.name for field in TicketType._meta.fields]


class FareBreakupAdmin(ImportExportModelAdmin, ModelAdmin):
    list_display = [field.name for field in FareBreakup._meta.fields]


class TicketRecommendationAdmin(ImportExportModelAdmin, ModelAdmin):
    list_display = [field.name for field in TicketRecommendation._meta.fields]
    search_fields = ("created_for__username",)
    readonly_fields = (
        "created_for",
    )
    autocomplete_fields = (
        "created_for",
    )


admin.site.register(Ticket, TicketAdmin)
admin.site.register(TicketUpdate, TicketUpdateAdmin)
admin.site.register(TicketType, TicketTypeAdmin)
admin.site.register(FareBreakup, FareBreakupAdmin)
admin.site.register(TicketRecommendation, TicketRecommendationAdmin)
