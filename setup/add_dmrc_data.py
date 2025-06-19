import csv
import logging

if __name__ == '__main__':
    import django

    django.setup()

from ondc_micromobility_api.models import MetroStation, FareMatrix

from ondc_micromobility_api.models import SystemParameters as dmrc_ticketing_api_SystemParameters

logger = logging.getLogger(__name__)


def read_gtfs_stops(file_path):
    gtfs_stops_list = []
    with open(file_path, 'r') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            gtfs_stops_list.append(row)
    return gtfs_stops_list


def main(testing=False):
    print("Populating MetroStation data...")
    MetroStation.populate_db()
    if not testing:
        # Read GTFS stops data
        file_path = "ondc_micromobility_api/data/gtfs/stops.txt"
        gtfs_stops_list = read_gtfs_stops(file_path)
        MetroStation.update_all_stations_from_gtfs(gtfs_stops_list)

        # update slugs
        MetroStation.update_all_stations_slugs()

    print("\nPopulating FareMatrix data...")
    if not testing:
        FareMatrix.populate_db(testing)

    print("\nPopulating ondc_micromobility_api SystemParameters data...")
    dmrc_ticketing_api_SystemParameters.populate_db()

    print("\nDatabase setup completed!")


if __name__ == '__main__':
    main()
