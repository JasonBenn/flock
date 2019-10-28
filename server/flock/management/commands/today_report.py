from datetime import datetime
from datetime import time
from datetime import timedelta

import pytz
from dateutil import rrule
from django.core.management.base import BaseCommand
from tqdm import tqdm

from flock.algorithm import get_location_to_people
from flock.management.commands.maybe_post_chill_times import already_posted_today
from flock.models import Location
from flock.utils import friendly_time, now


class Command(BaseCommand):
    def handle(self, *args, **options):
        days_ago = 15  # CONFIGURE
        day = (now() - timedelta(days=days_ago)).date()
        start_day = datetime.combine(day, time(hour=5), tzinfo=pytz.UTC)
        end_day = datetime.combine(now().date(), time(hour=23), tzinfo=pytz.UTC)
        common_room = Location.objects.get(name="Common room")

        for current_dt in tqdm(list(rrule.rrule(rrule.MINUTELY, interval=2, dtstart=start_day, until=end_day))):
            if already_posted_today():
                continue

            people = get_location_to_people(current_dt).get(common_room)
            if len(people) >= 5:
                print(f"{friendly_time(current_dt)}\t{len(people)}")
                *people, last_person = [x.first_name for x in people]
                message = f"@here chill times in the common room (with {', '.join(people)} and {last_person})"
                print(message)
