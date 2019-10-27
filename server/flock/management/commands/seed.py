from django.core.management import BaseCommand
from django.db import transaction
from psqlextra.query import ConflictAction
from psqlextra.util import postgres_manager

from flock.models import Device
from flock.models import DeviceType
from flock.models import Location
from flock.models import CustomThreshold
from flock.models import Person
from flock.models import SensorReading
from flock.constants import MAX_THRESHOLD
from flock.utils import now

people_devices = {
    "Ben Mann": {DeviceType.PHONE: "3C:28:6D:2C:37:9F", DeviceType.TABLET: "34:42:62:70:4B:0A"},
    "Zain Shah": {},
    "Jason Benn": {
        DeviceType.PHONE: "40:4E:36:BF:9E:16",
        DeviceType.TABLET: "08:E6:89:AD:EE:43",
        DeviceType.LAPTOP: "20:C9:D0:48:F6:AA",
    },
    "Allie Miller": {DeviceType.PHONE: "40:83:1D:E5:71:C7"},
    "Tina Kim": {},
    "Taylor Rogalski": {DeviceType.PHONE: "E0:33:8E:5F:7C:04"},
    "Josh Albrecht": {},
    "Kanjun Qiu": {},
    "Michael Lai": {DeviceType.PHONE: "AA:AA:AA:AA:AA:AA"},
    "Danielle Forward": {},
    "Beth Barnes": {DeviceType.PHONE: "08:D4:6A:18:81:45"},
    "Chris Varenhorst": {},
    "Rilka Li": {},
    "Laura D'Asaro": {},
    "Tommy Collison": {},
    "Arram Sabeti": {DeviceType.PHONE: "94:F6:D6:6A:60:00"},
    "Austin Hou": {DeviceType.PHONE: "94:65:2D:C6:C7:F6", DeviceType.LAPTOP: "8C:85:90:3C:FB:73"},
    "Annie Brett": {DeviceType.PHONE: "0C:CB:85:56:D2:B1"},
    "Rose Wang": {},
    "Jay Graber": {},
    "Bill Brett": {},
    "Danny Hernandez": {},
    "Alex Matzner": {},
    "Nish Bhat": {},
    "Diane Wu": {},
    "Anand Sharma": {},
}


class Command(BaseCommand):
    def handle(self, *args, **options):
        persons = [
            {"first_name": name[0], "last_name": name[1]} for name in [x.split(" ") for x in people_devices.keys()]
        ]

        with postgres_manager(Person) as manager:
            manager.on_conflict(["first_name", "last_name"], ConflictAction.NOTHING).bulk_insert(persons)

        people_to_ids = {
            (x["first_name"], x["last_name"]): x["id"] for x in Person.objects.values("id", "first_name", "last_name")
        }

        devices = []
        for person_name, devices_map in people_devices.items():
            person_id = people_to_ids[tuple(person_name.split(" "))]
            for device_type, mac in devices_map.items():
                devices.append({"mac": mac, "device_type": device_type, "person_id": person_id})

        with postgres_manager(Device) as manager:
            manager.on_conflict(["mac"], ConflictAction.UPDATE).bulk_insert(devices)

        with postgres_manager(Location) as manager:
            manager.on_conflict(["id"], ConflictAction.UPDATE).bulk_insert(
                [
                    {"id": 1, "name": "Common room", "description": "Right upper corner of mantle"},
                    {"id": 2, "name": "Jason's room", "description": ""},
                    {"id": 3, "name": "Middle Kingdom kitchen", "description": ""},
                    {"id": 4, "name": "Study", "description": ""},
                    {"id": 5, "name": "Workshop/Arram's room", "description": ""},
                    {"id": 6, "name": "Backyard", "description": ""},
                    {"id": 7, "name": "Roof", "description": ""},
                ]
            )

        with postgres_manager(SensorReading) as manager:
            manager.on_conflict(["id"], ConflictAction.UPDATE).bulk_insert(
                [
                    {"id": 1, "device_id": 1, "rssi": 0, "location_id": 1, "created_at": now()},
                    {"id": 2, "device_id": 2, "rssi": 0, "location_id": 1, "created_at": now()},
                    {"id": 3, "device_id": 3, "rssi": 0, "location_id": 2, "created_at": now()},
                    {"id": 4, "device_id": 4, "rssi": 0, "location_id": 2, "created_at": now()},
                    {"id": 5, "device_id": 5, "rssi": 0, "location_id": 3, "created_at": now()},
                    {"id": 6, "device_id": 6, "rssi": -5, "location_id": 3, "created_at": now()},
                    {"id": 7, "device_id": 7, "rssi": 0, "location_id": 3, "created_at": now()},
                ]
            )

        with postgres_manager(CustomThreshold) as manager:
            manager.on_conflict(["id"], ConflictAction.UPDATE).bulk_insert(
                [
                    {
                        "id": 1,
                        "device": Device.objects.get(person__first_name="Michael", device_type=DeviceType.PHONE),
                        "person": None,
                        "threshold": MAX_THRESHOLD,
                        "location": Location.objects.get(name="Common room"),
                        "reason": "Michael usually charges his phone in the common room, so ignore it.",
                    },
                    {
                        "id": 2,
                        "device": None,
                        "person": Person.objects.get(first_name="Allie"),
                        "threshold": MAX_THRESHOLD,
                        "location": Location.objects.get(name="Jason's room"),
                        "reason": "Ignore when Allie's devices are in Jason's room.",
                    },
                    {
                        "id": 3,
                        "device": None,
                        "person": Person.objects.get(first_name="Jason"),
                        "threshold": MAX_THRESHOLD,
                        "location": Location.objects.get(name="Jason's room"),
                        "reason": "Ignore when Jason's devices are in Jason's room.",
                    },
                    {
                        "id": 4,
                        "device": None,
                        "person": Person.objects.get(first_name="Ben"),
                        "threshold": -5,
                        "location": Location.objects.get(name="Common room"),
                        "reason": "Ben is right underneath common room.",
                    },
                ]
            )

        print(Location.objects.all())
        print(Person.objects.all())
        print(Device.objects.all())
        print(SensorReading.objects.all())

        transaction.commit()
