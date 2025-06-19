import logging

from custom_cities.models import City

logger = logging.getLogger(__name__)


def add_cities():
    cities = [
        {"code": "BLR", "display_name": "Bengaluru", "country": "IN"},
        {"code": "DEL", "display_name": "New Delhi", "country": "IN"},
    ]

    for city_data in cities:
        city, created = City.objects.get_or_create(**city_data)
        if created:
            logger.info(f"City {city.display_name} created")
        else:
            logger.info(f"City {city.display_name} already exists")
