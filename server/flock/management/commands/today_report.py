from collections import defaultdict
from datetime import datetime
from datetime import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils.timezone import localtime


class Command(BaseCommand):
    def handle(self, *args, **options):
        days_ago = 0  # CONFIGURE
        day = (localtime() - timedelta(days=days_ago)).date()
        start_day = datetime.combine(day, time(hour=5), tzinfo=localtime().tzinfo)
        end_day = datetime.combine(day + timedelta(days=1), time(hour=5), tzinfo=localtime().tzinfo)
        current_dt = start_day
        while current_dt <= end_day:
            readings = get_current_readings(current_dt)
            found = {reading for reading in readings.values() if reading}
            if len(found) > 1:
                grouped = defaultdict(list)
                for reading in found:
                    grouped[reading.location.name].append(reading.device.person.name)

                if max([len(x) for x in grouped.values()]) > 1:
                    print(
                        current_dt.strftime("%-I:%M%p") + "\t",
                        len(found),
                        max(len(v) for k, v in grouped.items()),
                        grouped,
                    )

            current_dt += timedelta(minutes=10)
