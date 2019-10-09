from datetime import timedelta

import sentry_sdk
from django.core.management.base import BaseCommand
from django.utils.timezone import localtime

from flock.models import SensorReading


class Command(BaseCommand):
    def handle(self, *args, **options):
        most_recent_readings = SensorReading.objects.raw('select distinct on ("location_id") "location_id", "id", "created_at" from flock_sensorreading order by "location_id", "created_at" desc;')
        quiet_devices = [x for x in most_recent_readings if localtime() - timedelta(hours=3) > x.created_at]
        for reading in sorted(quiet_devices, key=lambda x: x.created_at):
            error = f"No reading since {reading.created_at.strftime('%-m/%-d %-I:%M %p')}: {reading.location} "
            sentry_sdk.capture_exception(Exception(error))
