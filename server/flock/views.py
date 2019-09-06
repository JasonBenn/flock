import json
from collections import defaultdict
from datetime import timedelta

from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from flock.models import Device
from flock.models import Location
from flock.models import Person
from flock.models import Position
from flock.utils import now


def index(request):
    people_by_location = defaultdict(list)
    for person in Person.objects.filter(location__isnull=False):
        people_by_location[person.location].append(person.name)

    return render(request, "index.html", {"people_by_location": dict(people_by_location)})


def macs(request):
    return JsonResponse({"macs": [x.mac for x in Device.objects.all()]})


@csrf_exempt
@transaction.atomic
def scans(request):
    data = json.loads(request.body)
    location = data["location"]

    # Append scans to Positions table
    people_by_mac = {x.mac: x.person for x in Device.objects.all()}
    locations_by_id = {x.clean_name(): x for x in Location.objects.all()}

    positions = [Position(person=people_by_mac[mac], location=locations_by_id[location]) for mac in data["macs"]]
    Position.objects.bulk_create(positions)

    # Update Person table with current positions
    people = list(Person.objects.all())
    existing_location_by_person_id = {x.id: x.location_id for x in people}

    current_positions = (
        Position.objects.filter(created_at__gt=now() - timedelta(minutes=60))
        .order_by("created_at")
        .values("person_id", "location_id")
        .annotate(Max("created_at"))
    )

    new_location_by_person_id = {x.id: None for x in people}
    for x in current_positions:
        new_location_by_person_id[x["person_id"]] = x["location_id"]

    for person_id, existing_location_id in existing_location_by_person_id.items():
        new_location_id = new_location_by_person_id[person_id]
        if new_location_id != existing_location_id:
            Person.objects.filter(id=person_id).update(location_id=new_location_id)
            print(f"changed: {existing_location_id} -> {new_location_id}")

    return HttpResponse(status=204)
