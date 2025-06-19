from django.contrib import admin

from transit.models.transit_setup import TransitOption, TransitProvider, ServiceCalendar, CalendarDate
from transit.models.trip_setup import Trip


class ServiceCalendarAdmin(admin.ModelAdmin):
    list_display = ('transit_option', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ('transit_option__name',)  # Adjust field according to your TransitOption model.
    fieldsets = (
        (None, {
            'fields': ('transit_option', 'monday', 'tuesday', 'wednesday',
                       'thursday', 'friday', 'saturday', 'sunday')
        }),
        ('Date Range', {
            'fields': ('start_date', 'end_date')
        }),
        ('Monday', {
            'fields': ('monday_start_time', 'monday_end_time')
        }),
        ('Tuesday', {
            'fields': ('tuesday_start_time', 'tuesday_end_time')
        }),
        ('Wednesday', {
            'fields': ('wednesday_start_time', 'wednesday_end_time')
        }),
        ('Thursday', {
            'fields': ('thursday_start_time', 'thursday_end_time')
        }),
        ('Friday', {
            'fields': ('friday_start_time', 'friday_end_time')
        }),
        ('Saturday', {
            'fields': ('saturday_start_time', 'saturday_end_time')
        }),

        ('Sunday', {
            'fields': ('sunday_start_time', 'sunday_end_time')
        })
    )


class ServiceCalendarInline(admin.StackedInline):
    model = ServiceCalendar
    can_delete = False
    verbose_name_plural = 'Service Calendar'
    fieldsets = (
        ('Dates', {
            'fields': ('start_date', 'end_date'),
        }),
        ('Monday', {
            'fields': ('monday', 'monday_start_time', 'monday_end_time'),
            'classes': ('collapse',),
        }),
        ('Tuesday', {
            'fields': ('tuesday', 'tuesday_start_time', 'tuesday_end_time'),
            'classes': ('collapse',),
        }),
        ('Wednesday', {
            'fields': ('wednesday', 'wednesday_start_time', 'wednesday_end_time'),
            'classes': ('collapse',),
        }),
        ('Thursday', {
            'fields': ('thursday', 'thursday_start_time', 'thursday_end_time'),
            'classes': ('collapse',),
        }),
        ('Friday', {
            'fields': ('friday', 'friday_start_time', 'friday_end_time'),
            'classes': ('collapse',),
        }),
        ('Saturday', {
            'fields': ('saturday', 'saturday_start_time', 'saturday_end_time'),
            'classes': ('collapse',),
        }),
        ('Sunday', {
            'fields': ('sunday', 'sunday_start_time', 'sunday_end_time'),
            'classes': ('collapse',),
        }),
    )


class TransitOptionAdmin(admin.ModelAdmin):
    inlines = (ServiceCalendarInline,)
    list_display = ('provider', 'transit_mode')
    search_fields = ['provider__name']


class TransitProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'logo_url')
    search_fields = ['name']


admin.site.register(Trip)
admin.site.register(CalendarDate)
admin.site.register(ServiceCalendar, ServiceCalendarAdmin)
admin.site.register(TransitOption, TransitOptionAdmin)
admin.site.register(TransitProvider, TransitProviderAdmin)
