from django.db import transaction
from psqlextra.query import ConflictAction
from psqlextra.util import postgres_manager

from flock.models import Device, Location
from flock.models import Person


people_devices = {
    "Ben Mann": {"Pixel": "3C:28:6D:2C:37:9F", "iPad": "34:42:62:70:4B:0A"},
    "Zain Shah": {},
    "Jason Benn": {"Pixel": "40:4E:36:BF:9E:16", "iPad": "08:E6:89:AD:EE:43", "MBP": "20:C9:D0:48:F6:AA"},
    "Allie Miller": {"iPhone": "40:83:1D:E5:71:C7"},
    "Tina Kim": {},
    "Taylor Rogalski": {"phone": "E0:33:8E:5F:7C:04"},
    "Josh Albrecht": {},
    "Kanjun Qiu": {},
    "Michael Lai": {},
    "Danielle Forward": {},
    "Beth Barnes": {"phone": "08:D4:6A:18:81:45"},
    "Chris Varenhorst": {},
    "Rilka Li": {},
    "Laura D'Asaro": {},
    "Tommy Collison": {},
    "Arram Sabeti": {"iPhone": "94:F6:D6:6A:60:00"},
    "Austin Hou": {"Android": "94:65:2D:C6:C7:F6", "laptop": "8C:85:90:3C:FB:73"},
    "Annie Brett": {"phone": "0C:CB:85:56:D2:B1"},
    # "Rose Wang": {},
    # "Jay Graber": {},
    # "Bill Brett": {},
    # "Danny Hernandez": {},
    # "Alex Matzner": {},
    # "Nish Bhat": {},
    # "Diane Wu": {},
    # "Anand Sharma": {},
}

persons = [{"first_name": name[0], "last_name": name[1]} for name in [x.split(" ") for x in people_devices.keys()]]

with postgres_manager(Person) as manager:
    manager.on_conflict(["first_name", "last_name"], ConflictAction.NOTHING).bulk_insert(persons)

people_to_ids = {
    (x["first_name"], x["last_name"]): x["id"] for x in Person.objects.values("id", "first_name", "last_name")
}

devices = []
for person_name, devices_map in people_devices.items():
    person_id = people_to_ids[tuple(person_name.split(" "))]
    for device_name, device_mac in devices_map.items():
        devices.append({"mac": device_mac, "name": device_name, "person_id": person_id})

with postgres_manager(Device) as manager:
    manager.on_conflict(["mac"], ConflictAction.UPDATE).bulk_insert(devices)


# with postgres_manager(Location) as manager:
#     manager.on_conflict(["id"], ConflictAction.UPDATE).bulk_insert([
#         {"name": "Common room", "description": "Right upper corner of mantle"},
#         {"name": "Jason's room", "description": ""},
#         {"name": "Middle Kingdom kitchen", "description": ""},
#         {"name": "Study", "description": ""},
#         {"name": "Workshop/Arram's room", "description": ""},
#         {"name": "Backyard", "description": ""},
#         {"name": "Roof", "description": ""},
#     ])
# print(Location.objects.all())

print(Person.objects.all())
print(Device.objects.all())

transaction.commit()
