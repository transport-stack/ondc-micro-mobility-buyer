from dateutil import parser
import pytz
from geopy.distance import geodesic
from modules.logger_main import logger


def convert_to_unix_timestamp(timestamp_str):
    try:
        # Use dateutil to parse the timestamp string
        dt = parser.isoparse(timestamp_str)
        # Ensure it is in UTC timezone
        dt = dt.astimezone(pytz.UTC)
        # Convert to Unix timestamp
        unix_timestamp = int(dt.timestamp())
        return unix_timestamp
    except Exception as e:
        logger.error(f"Failed to convert timestamp {timestamp_str}: {e}")
        raise ValueError(f"Invalid timestamp format: {timestamp_str}")


def calculate_distance(lat1, lon1, lat2, lon2):
    try:
        point1 = (lat1, lon1)
        point2 = (lat2, lon2)
        distance = geodesic(point1, point2).kilometers
        return distance
    except Exception as e:
        logger.error(f"Error calculating distance between {point1} and {point2}: {e}")
        raise
