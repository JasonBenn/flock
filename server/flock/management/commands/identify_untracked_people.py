from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils.functional import partition

from flock.models import Person, Room, Device
from flock.models import SensorReading
from flock.utils import now


class Command(BaseCommand):
    def handle(self, *args, **options):
        most_recent_readings = {}
        for person in Person.objects.filter(active=True):
            max_created_at = SensorReading.objects.filter(person=person, present=True).aggregate(Max("created_at"))[
                "created_at__max"
            ]
            if max_created_at and max_created_at < now() - timedelta(days=7):
                most_recent_readings[person] = max_created_at

        quiet_people = {
            person: last_reading
            for person, last_reading in most_recent_readings.items()
            if last_reading and now() - timedelta(hours=3) > last_reading
        }

        residents, non_residents = partition(lambda x: x.room == Room.NONE, quiet_people.keys())

        print("Residents:")
        for person in sorted(residents, key=lambda x: quiet_people[x]):
            last_reading = quiet_people[person]
            day = last_reading.strftime("%-m/%-d")
            time = last_reading.strftime("%-I:%M %p")
            print(f"{day:>5} {time:>8}  {person}")

        print("\nNon-residents:")
        for person in sorted(non_residents, key=lambda x: quiet_people[x]):
            last_reading = quiet_people[person]
            day = last_reading.strftime("%-m/%-d")
            time = last_reading.strftime("%-I:%M %p")
            print(f"{day:>5} {time:>8}  {person}")

        print("People with no devices:")
        device_people_ids = set(Device.objects.values_list("person_id", flat=True))
        people_ids = set(Person.objects.values_list("id", flat=True))
        no_device_people_ids = people_ids - device_people_ids
        for person in Person.objects.filter(id__in=no_device_people_ids).order_by("first_name"):
            print(person)
