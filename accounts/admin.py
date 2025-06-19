from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from accounts.models.user_setup import MyUser


class MyUserAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    # show created_at and updated_at fields
    readonly_fields = ("created_at", "updated_at")
    # add search fields
    search_fields = (
        "username",
        "email",
    )
    # add filter fields, with date
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
    )
    # add list display fields
    list_display = (
        "username",
        "email",
        "is_active",
        "is_staff",
        "is_superuser",
        "created_at",
        "updated_at",
    )


admin.site.register(MyUser, MyUserAdmin)
