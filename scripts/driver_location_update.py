import time

from geopy.distance import geodesic


def interpolate_coordinates(start_lat, start_lon, end_lat, end_lon, current_step, total_steps):
    fraction = current_step / total_steps

    # Interpolate latitude and longitude
    lat = start_lat + fraction * (end_lat - start_lat)
    lon = start_lon + fraction * (end_lon - start_lon)

    return lat, lon

