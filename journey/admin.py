from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import DateRangeFilterBuilder

from journey.models.journey_setup import Journey


# Register your models here.


class JourneyAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    autocomplete_fields = ["tickets"]
    list_display = ("uuid", "link_to_created_for", "created_at", "status")
    list_filter = (
        "status",
        ("created_at", DateRangeFilterBuilder()),
    )
    search_fields = ("uuid", "created_for__username", "tickets__pnr")
    readonly_fields = (
        "uuid",
        "created_at",
        "updated_at",
        "created_by", "created_for"
    )
    fieldsets = (
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                ),
            },
        ),
        (
            "Journey Data",
            {
                "fields": (
                    "uuid",
                    "data",
                    "status",
                    "tickets",
                ),
            },
        ),
        (
            "Users",
            {
                "fields": (
                    "created_by",
                    "created_for",
                ),
            },
        ),
    )

    def link_to_created_for(self, obj):
        link = reverse(
            "admin:%s_%s_change"
            % (obj.created_for._meta.app_label, obj.created_for._meta.model_name),
            args=[obj.created_for.id],
        )
        return format_html('<a href="{}">{}</a>', link, obj.created_for)

    link_to_created_for.short_description = "Created For"


admin.site.register(Journey, JourneyAdmin)
