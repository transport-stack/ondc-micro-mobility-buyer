from _decimal import Decimal
from django.db import transaction

if __name__ == '__main__':
    import os
    import django

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.base')
    django.setup()

import csv

from ondc_micromobility_api.models import MetroStation

# Add logging for audit
updated_stations = []
skipped_stations = []

with open('ondc_micromobility_api/data/gtfs/stops.txt', 'r') as file:
    reader = csv.DictReader(file)
    correct_names = {(float(row['stop_lat']), float(row['stop_lon'])): row['stop_name'] for row in reader}

with transaction.atomic():  # Ensures all updates are done in a single transaction
    for station in MetroStation.objects.all():
        if not station.lat or not station.lon:
            skipped_stations.append(station.station_id)
            continue

        tolerance = Decimal('0.001')
        nearest_name, min_distance = min(
            [(name, abs(station.lat - Decimal(str(lat))) + abs(station.lon - Decimal(str(lon))))
             for (lat, lon), name in correct_names.items()],
            key=lambda x: x[1],
            default=(None, Decimal('inf'))
        )

        if nearest_name and min_distance < tolerance:
            station.name = nearest_name
            station.save()
            updated_stations.append(station.station_id)
        else:
            skipped_stations.append(station.station_id)

# Log or print the results
print(f"Updated stations: {updated_stations}")
print(f"Skipped stations: {skipped_stations}")
