from django.contrib import admin

from common.models import SystemParameters


def mark_as_inactive(modeladmin, request, queryset):
    queryset.update(active=False)


mark_as_inactive.short_description = "Mark selected rows as inactive"


def mark_as_active(modeladmin, request, queryset):
    queryset.update(active=True)


mark_as_active.short_description = "Mark selected rows as active"


@admin.register(SystemParameters)
class SystemParametersAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    class Meta:
        model = SystemParameters
        verbose_name_plural = "System Parameters"
