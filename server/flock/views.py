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
from flock.models import Position
from flock.utils import now


def get_current_positions():
    return Position.objects.filter(created_at__gt=now() - timedelta(minutes=10)).values("person__first_name", "person__last_name", "location_id").annotate(updated_at=Max("created_at"))


def index(request):
    people_by_location = defaultdict(dict)
    for position in get_current_positions():
        time = now()
        if position["updated_at"] > (time - timedelta(minutes=3)):
            color = "black"
        elif position["updated_at"] > (time - timedelta(minutes=6)):
            color = "darkgray"
        else:
            color = "lightgray"
        person_name = position["person__first_name"] + " " + position["person__last_name"][0]
        location = Location.objects.get(id=position["location_id"])
        people_by_location[location][person_name] = color

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

    return HttpResponse(status=204)
