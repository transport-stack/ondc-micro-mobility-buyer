from django.contrib import admin

from common.admin import mark_as_inactive, mark_as_active
from ondc_micromobility_api.models import FareMatrix, MetroStation, SystemParameters
from import_export.admin import ImportExportModelAdmin
from django.utils.translation import gettext_lazy as _


class MetroStationAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    search_fields = ['name']
    list_display = ("station_id", "name", "lat", "lon", "active")
    readonly_fields = ('station_id',)
    actions = [mark_as_inactive, mark_as_active]


class SourceStationFilter(admin.SimpleListFilter):
    title = _('Source Station')
    parameter_name = 'source_station'

    def lookups(self, request, model_admin):
        stations = MetroStation.objects.all()
        return [(station.station_id, station.name) for station in stations]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(source_station__station_id=self.value())
        return queryset


class DestinationStationFilter(admin.SimpleListFilter):
    title = _('Destination Station')
    parameter_name = 'destination_station'

    def lookups(self, request, model_admin):
        stations = MetroStation.objects.all()
        return [(station.station_id, station.name) for station in stations]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(destination_station__station_id=self.value())
        return queryset


class FareMatrixAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    list_display = ("get_source_station_name", "get_destination_station_name", "fare")
    list_filter = (SourceStationFilter, DestinationStationFilter,)
    autocomplete_fields = ['source_station', 'destination_station']

    class Meta:
        verbose_name = "Fare Matrix"
        verbose_name_plural = "Fare Matrices"

    def get_source_station_name(self, obj):
        return obj.source_station.name

    get_source_station_name.short_description = "Source Station"

    def get_destination_station_name(self, obj):
        return obj.destination_station.name

    get_destination_station_name.short_description = "Destination Station"


admin.site.register(SystemParameters)
admin.site.register(FareMatrix, FareMatrixAdmin)
admin.site.register(MetroStation, MetroStationAdmin)
