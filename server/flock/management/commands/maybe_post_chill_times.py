import json
import os
from typing import List

import requests
from django.core.management import BaseCommand
from requests import Response

from flock.algorithm import get_location_to_people
from flock.models import ChillTime, Location, Person
from flock.models import ChillTimesThreshold
from flock.utils import as_pdt, now, title_case
from flock.utils import post_slack


class Command(BaseCommand):
    def handle(self, *args, **options):
        for chill_times_threshold in ChillTimesThreshold.objects.all():
            location = chill_times_threshold.location

            if already_posted_today(location):
                print("Already posted today!")
                continue

            people = get_location_to_people().get(location, [])
            if len(people) >= chill_times_threshold.threshold:
                response = post_chill_times(location, people)
                if response.status_code == 200:
                    ChillTime.objects.create(person_ids=[x.id for x in people], location=location)
                    print("Created ChillTime!")
                else:
                    print("Something went wrong...!")
            else:
                print(f"Only saw {len(people)}, wanted {chill_times_threshold.threshold} for {location.name}, not POSTing.")


def already_posted_today(location: Location) -> bool:
    last_post = ChillTime.objects.filter(location=location).last()
    if not last_post:
        return False
    last_post_created_at = last_post.created_at
    return as_pdt(last_post_created_at).date() == as_pdt(now()).date()


def post_chill_times(location: Location, people: List[Person]) -> Response:
    *people_head, last_person = [x.first_name for x in people]
    message = (
        f"<!here> chill times in the {title_case(location.name)} with {', '.join(people_head)} and {last_person}!"
    )
    return post_slack(message, "chill-times")
