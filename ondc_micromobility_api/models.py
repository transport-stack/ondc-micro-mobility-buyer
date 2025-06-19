import csv
import logging
import time

import django_filters
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Count
from django.template.defaultfilters import slugify
# from fuzzywuzzy import process

from common.models import SingletonBaseModel
from ondc_micromobility_api.ondc_wrapper.models.common import Station
from modules.models import ActiveMixin, DateTimeMixin


# Create your models here.
class SystemParameters(SingletonBaseModel):
    active = models.BooleanField(default=True, help_text="Is ticketing enabled?")

    ticket_confirmation_timeout = models.PositiveIntegerField(
        default=120,  # Default timeout of 120 seconds
        help_text="Timeout for ticket confirmation (seconds)"
    )

    repeat_ticketing_cooldown_period = models.PositiveIntegerField(
        default=5400,  # Default timeout of 120 seconds
        help_text="Repeat ticketing cooldown period (seconds)"
    )

    metro_stations_last_modified = models.BigIntegerField(
        default=1706689529,
        help_text="Timestamp of last modification of Metro Stations data"
    )

    # HTML content for QR code label
    qr_label_message = models.TextField(
        default="Scan this QR code at the entry gate booking",
        help_text="HTML content for QR code label"
    )

    max_passengers_per_ticket = models.PositiveIntegerField(
        default=1,
        help_text="Maximum number of passengers per ticket"
    )

    report_to = models.TextField(
        null=True,
        blank=True,
        help_text="Comma-separated list of emails to send reports to"
    )

    report_cc = models.TextField(
        null=True,
        blank=True,
        help_text="Comma-separated list of emails to CC in reports"
    )
    service_enabled = models.BooleanField(default=True, help_text="Is service enabled?")
    service_message = models.TextField(default="", help_text="Message to show when service is disabled")

    class Meta:
        verbose_name = "System Parameter"
        verbose_name_plural = "System Parameters"

    def __str__(self):
        return "System Parameters"

    def get_report_cc(self):
        if self.report_cc:
            return self.report_cc.strip()

        return None

    def get_report_to(self):
        if self.report_to:
            return self.report_to.strip()

        return None

    @staticmethod
    def update_metro_stations_last_modified():
        params = SystemParameters.load()
        params.metro_stations_last_modified = int(time.time())
        params.save()

    @staticmethod
    def populate_db():
        # Check if there's already an instance
        if not SystemParameters.objects.exists():
            SystemParameters.objects.create()
            logging.info("SystemParameters instance created with default values.")
        else:
            logging.info("SystemParameters instance already exists.")

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


def station_name_slugify(name: str) -> str:
    return slugify(name)


class MetroStation(ActiveMixin, DateTimeMixin):
    station_id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, null=True, default=None, blank=True)
    lat = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        default=None,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    lon = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        default=None,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )
    gtfs_stop_id = models.CharField(max_length=16, null=True, default=None, blank=True)
    slug = models.SlugField(max_length=255, null=True, default=None, blank=True)

    class Meta:
        verbose_name = "Metro Station"
        verbose_name_plural = "Metro Stations"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.station_id})"

    @classmethod
    def from_station(cls, station: Station) -> "MetroStation":
        return cls.objects.update_or_create(
            station_id=station.station_ID,
            defaults={
                'name': station.station_Name,
                'location': station.station_Location
            }
        )[0]

    @staticmethod
    def populate_db():
        client = RouteRequestAPI()
        response_obj = client.post_api()

        if response_obj and response_obj.is_success():
            existing_station_ids = set(MetroStation.objects.values_list('station_id', flat=True))
            to_create = []
            to_update = []

            station_details = response_obj.get_station_details()
            for station_data in station_details:
                for station in station_data:
                    station_obj = Station.from_dict({
                        "station_ID": station.station_ID,
                        "station_Name": station.station_Name,
                        "station_Location": station.station_Location
                    })

                    if station_obj.station_ID in existing_station_ids:
                        existing_station = MetroStation.objects.get(station_id=station_obj.station_ID)
                        existing_station.name = station_obj.station_Name
                        existing_station.location = station_obj.station_Location
                        to_update.append(existing_station)
                    else:
                        to_create.append(
                            MetroStation(
                                station_id=station_obj.station_ID,
                                name=station_obj.station_Name,
                                location=station_obj.station_Location
                            )
                        )

            # Use bulk_create for new records
            MetroStation.objects.bulk_create(to_create, ignore_conflicts=True)

            # Use bulk_update for existing records
            if to_update:
                MetroStation.objects.bulk_update(to_update, ['name', 'location'])

    @staticmethod
    def update_lat_lon_from_csv():
        try:
            with open('ondc_micromobility_api/data/dmrc_metrostation_lat_lon.csv', 'r') as csv_file:
                reader = csv.DictReader(csv_file)

                for row in reader:
                    try:
                        station_id = int(row["station_id"])
                        lat = float(row["lat"]) if row["lat"] else None
                        lon = float(row["lon"]) if row["lon"] else None

                        # Update the MetroStation object
                        MetroStation.objects.filter(station_id=station_id).update(lat=lat, lon=lon)
                        logging.debug(f"Updated lat/lon: {lat}/{lon} for station_id: {station_id}")
                    except ValueError as e:
                        logging.error(f"Error while updating lat/lon for station_id: {row['station_id']} - {e}")
                        # handle any data type conversion errors
                        continue
        except Exception as e:
            logging.error(f"Error while updating lat/lon from csv - {e}")

    def update_from_gtfs_match(self, gtfs_stops_list):
        """update the current MetroStation instance with data from the best match GTFS stop"""
        try:
            # Extract names from GTFS stops list for fuzzy matching
            gtfs_names = [stop['stop_name'] for stop in gtfs_stops_list]

            # Find the best match in GTFS stops list
            # best_match_name, _ = process.extractOne(self.name, gtfs_names)

            # Find the GTFS stop that matches the best_match_name
            # best_match_stop = next((stop for stop in gtfs_stops_list if stop['stop_name'] == best_match_name), None)

            # if best_match_stop:
            #     # Update current MetroStation instance with data from best match GTFS stop
            #     self.gtfs_stop_id = best_match_stop.get('stop_id')
            #     self.lat = float(best_match_stop['stop_lat']) if best_match_stop.get('stop_lat') else None
            #     self.lon = float(best_match_stop['stop_lon']) if best_match_stop.get('stop_lon') else None
            #     self.save()
            #     logging.debug(
            #         f"Updated MetroStation: {self.name} (gtfs_stop_name: {best_match_name}, gtfs_stop_id: {self.gtfs_stop_id}) from GTFS data.")

        except Exception as e:
            logging.error(f"Error updating MetroStation from GTFS data - {e}")

    @staticmethod
    def update_all_stations_from_gtfs(gtfs_stops_list):
        # Update each MetroStation object with GTFS data
        for metro_station in MetroStation.objects.filter(active=True).all():
            metro_station.update_from_gtfs_match(gtfs_stops_list)

    @staticmethod
    def update_all_stations_slugs():
        # Update slug for each MetroStation object
        for metro_station in MetroStation.objects.filter(active=True).all():
            metro_station.update_slug()

        # check if there are duplicate slugs
        # if yes, append station_id to slug
        duplicate_slugs = MetroStation.objects.values('slug').annotate(count=Count('slug')).filter(count__gt=1)
        for duplicate_slug in duplicate_slugs:
            stations = MetroStation.objects.filter(slug=duplicate_slug['slug'])
            for station in stations:
                station.slug = f"{station.slug}-{station.station_id}"
                station.save()
                logging.debug(f"Updated slug for MetroStation: {station.name} (/{station.slug})")

    def get_slug(self):
        if self.slug:
            return self.slug
        return station_name_slugify(f"{self.name}")

    def update_slug(self):
        self.slug = station_name_slugify(f"{self.name}")
        logging.debug(f"Updated slug for MetroStation: {self.name} (/{self.slug})")
        self.save()

    def save(self, *args, **kwargs):
        SystemParameters.update_metro_stations_last_modified()
        super().save(*args, **kwargs)


class MetroStationFilter(django_filters.FilterSet):
    name_contains = django_filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = MetroStation
        fields = ['name_contains']


class FareMatrix(DateTimeMixin, ActiveMixin):
    source_station = models.ForeignKey(MetroStation, related_name='source_fares', on_delete=models.CASCADE)
    destination_station = models.ForeignKey(MetroStation, related_name='destination_fares', on_delete=models.CASCADE)
    fare = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('source_station', 'destination_station')
        verbose_name_plural = "Fare Matrices"

    @staticmethod
    def populate_db(testing=False):
        # Delete all rows from FareMatrix
        FareMatrix.objects.all().delete()

        all_metro_stations = MetroStation.objects.all()
        # Create a mapping of station_id to MetroStation objects to reduce DB queries
        metro_stations_mapping = {station.station_id: station for station in MetroStation.objects.all()}

        if testing:
            # TODO: WIP
            # 188 is the test source station in test case test_ticket_initiate
            all_metro_stations = [MetroStation.objects.get(station_id=188)]

        for metro_station in all_metro_stations:
            client = FareFromSourceToAllDestinationsAPI(stationID=metro_station.station_id)
            response_obj = client.post_api()

            if response_obj and response_obj.is_success():
                for fare_detail in response_obj.objSourecToDestination:
                    source = metro_stations_mapping[fare_detail['fromStationID']]
                    destination = metro_stations_mapping[fare_detail['toStationID']]

                    if source != destination:  # Making sure source and destination are different
                        fare = fare_detail['fare'] / 100.0
                        fare_matrix = FareMatrix.objects.create(
                            source_station=source,
                            destination_station=destination,
                            fare=fare
                        )

    @staticmethod
    def get_fare_inr_between_source_station_and_destination_station(source_station_id, destination_station_id):
        fare_obj = FareMatrix.get_fare_obj_between_source_station_and_destination_station(source_station_id,
                                                                                          destination_station_id)
        if fare_obj:
            return fare_obj.fare
        else:
            return None

    @staticmethod
    def get_fare_obj_between_source_station_and_destination_station(source_station_id, destination_station_id):
        try:
            return FareMatrix.objects.get(source_station__station_id=source_station_id,
                                          destination_station__station_id=destination_station_id)
        except FareMatrix.DoesNotExist:
            return None
