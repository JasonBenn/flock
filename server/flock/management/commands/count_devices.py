from collections import defaultdict

from django.core.management.base import BaseCommand

from flock.models import Device
from flock.models import DeviceType
from flock.models import Person


class Command(BaseCommand):
    def handle(self, *args, **options):
        archivists = Person.objects.exclude(first_name__in=["Robin", "YC", "Akiva"])
        people_to_phones = defaultdict(list)
        for device in Device.objects.filter(device_type=DeviceType.PHONE, person__in=archivists):
            people_to_phones[device.person].append(device)

        people_to_laptops = defaultdict(list)
        for device in Device.objects.filter(device_type__in=[DeviceType.LAPTOP, DeviceType.WORK_LAPTOP], person__in=archivists):
            people_to_laptops[device.person].append(device)

        missing_phones = {x for x in archivists if x not in people_to_phones}
        missing_laptops = {x for x in archivists if x not in people_to_laptops}
        person_count = Person.objects.count()
        print(
            f"Missing {len(missing_phones) / person_count*100:.0f}% of phones ({', '.join(sorted(x.first_name for x in missing_phones))})"
        )
        print(
            f"Missing {len(missing_laptops) / person_count*100:.0f}% of laptops ({', '.join(sorted(x.first_name for x in missing_laptops))})"
        )
        print(f"Total devices: {Device.objects.count()}")
