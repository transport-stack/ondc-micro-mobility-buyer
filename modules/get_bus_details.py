from django.core.cache import cache
import json


def fetch_vehicle_data(vehicle_id):
    fleet_data_cache_key = "fleet_data"
    vehicle_list = cache.get(fleet_data_cache_key)
    for vehicle in vehicle_list:
        if vehicle['vehicle_id'] == vehicle_id:
            return vehicle
    return None
