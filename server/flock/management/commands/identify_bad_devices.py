from datetime import timedelta
from operator import itemgetter

import sentry_sdk
from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils.timezone import localtime

from flock.models import Location
from flock.models import SensorReading


class Command(BaseCommand):
    def handle(self, *args, **options):
        most_recent_readings = {}
        for location in Location.objects.all():
            most_recent_readings[location] = SensorReading.objects.filter(location=location).aggregate(Max('created_at'))['created_at__max']

        quiet_sensors = {location: last_reading for location, last_reading in most_recent_readings.items() if last_reading and localtime() - timedelta(hours=3) > last_reading}
        for location, last_reading in sorted(quiet_sensors.items(), key=itemgetter(1)):
            error = f"No reading from {location.name} since {last_reading.strftime('%-m/%-d %-I:%M %p')}"
            print(error)
            # sentry_sdk.capture_exception(Exception(error))
            print(f"ssh pi_{location.clean_name()} sudo systemctl start flock.service")
