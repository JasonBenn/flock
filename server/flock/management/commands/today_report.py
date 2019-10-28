from datetime import datetime
from datetime import time
from datetime import timedelta

import pytz
from dateutil import rrule
from django.core.management.base import BaseCommand
from tqdm import tqdm

from flock.algorithm import get_location_to_people
from flock.utils import friendly_time, now


class Command(BaseCommand):
    def handle(self, *args, **options):
        days_ago = 15  # CONFIGURE
        day = (now() - timedelta(days=days_ago)).date()
        start_day = datetime.combine(day, time(hour=5), tzinfo=pytz.UTC)
        end_day = datetime.combine(now().date(), time(hour=23), tzinfo=pytz.UTC)
        for current_dt in tqdm(list(rrule.rrule(rrule.MINUTELY, interval=15, dtstart=start_day, until=end_day))):
            location_to_people = get_location_to_people(current_dt)
            for location, people in location_to_people.items():
                if len(people) >= 5:
                    print(f"{friendly_time(current_dt)}\t{len(people)}")
                    *people, last_person = [x.first_name for x in people]
                    print(f"@here chill times in the common room (with {', '.join(people)} and {last_person})")
