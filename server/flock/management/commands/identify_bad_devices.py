from datetime import timedelta
from operator import itemgetter

from django.core.management.base import BaseCommand
from django.db.models import Max

from flock.models import Device
from flock.models import SensorReading
from flock.utils import now


class Command(BaseCommand):
    def handle(self, *args, **options):
        most_recent_readings = {}
        for device in Device.objects.all():
            max_created_at = SensorReading.objects.filter(device=device, present=True).aggregate(Max("created_at"))[
                "created_at__max"
            ]
            if max_created_at and max_created_at < now() - timedelta(days=7):
                most_recent_readings[device] = max_created_at

        quiet_devices = {
            device: last_reading
            for device, last_reading in most_recent_readings.items()
            if last_reading and now() - timedelta(hours=3) > last_reading
        }
        for device, last_reading in sorted(quiet_devices.items(), key=itemgetter(1)):
            day = last_reading.strftime("%-m/%-d")
            time = last_reading.strftime("%-I:%M %p")
            print(f"{day:>5} {time:>8}  {device}")
