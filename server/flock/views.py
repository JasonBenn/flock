import json
from collections import defaultdict
from datetime import timedelta
from typing import List

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from flock.models import Device, Person
from flock.models import Location
from flock.models import Position
from flock.utils import now


def get_current_positions():
    return (
        Position.objects.filter(created_at__gt=now() - timedelta(minutes=15))
        .values("person__first_name", "person__last_name", "location_id")
        .annotate(updated_at=Max("created_at"))
    )


def never_detected() -> str:
    detected = set(Position.objects.values_list("person_id", flat=True).distinct())
    people = set(Person.objects.values_list("id", flat=True).distinct())
    never_detected = people - detected
    return ", ".join(sorted([x.name for x in Person.objects.filter(id__in=never_detected)]))


@login_required
def index(request):
    user = request.user
    if user.username == "flock" or not user.is_authenticated:
        return redirect(login)
    people_by_location = defaultdict(dict)
    for position in get_current_positions():
        time = now()
        if position["updated_at"] > (time - timedelta(minutes=9)):
            color = "black"
        elif position["updated_at"] > (time - timedelta(minutes=12)):
            color = "darkgray"
        else:
            color = "lightgray"
        person_name = position["person__first_name"] + " " + position["person__last_name"][0]
        location = Location.objects.get(id=position["location_id"])
        people_by_location[location][person_name] = color

    return render(
        request,
        "index.html",
        {"people_by_location": dict(people_by_location), "never_detected": never_detected()},
    )


def login(request):
    return render(request, "login.html")


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

    positions = [
        Position(person=people_by_mac[mac], location=locations_by_id[location])
        for mac in data["macs"]
    ]
    Position.objects.bulk_create(positions)

    return HttpResponse(status=204)
