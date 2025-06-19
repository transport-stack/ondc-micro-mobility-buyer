from django.contrib import admin

# add city model
from custom_cities.models import City

# Register your models here.


admin.site.register(City)
