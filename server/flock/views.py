import json
from datetime import timedelta
from itertools import groupby
from typing import Dict
from typing import Optional

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.db.models import Q
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from flock.models import Device
from flock.models import Location
from flock.models import CustomThreshold
from flock.models import Person
from flock.models import SensorReading
from flock.utils import now

MAX_THRESHOLD = 100


PersonToReading = Dict[Person, Optional[SensorReading]]


def get_most_mobile_device(devices):
    return sorted(devices, key=lambda x: x.device_type)[0]


def get_current_readings() -> PersonToReading:
    current_readings_unhidden = get_current_readings_unhidden()
    overrides = get_matching_override_rules(current_readings_unhidden)
    return {**current_readings_unhidden, **overrides}


def get_matching_override_rules(person_readings: PersonToReading) -> PersonToReading:
    """
    Identifies the people whose location estimate should be hidden.
    Given a list of PersonToReading, return a subset that maps those people to None.
    """
    locations = [reading.location for person, reading in person_readings.items() if reading]
    override_rules = CustomThreshold.objects.filter(
        person__in=person_readings.keys(), location__in=locations
    ).select_related("device")

    hidden_people = {}
    for rule in override_rules:
        person = rule.person or (rule.device and rule.device.person)
        reading = person_readings.get(person)
        if not reading:
            continue
        about_them = (rule.device_id == reading.device_id) or (rule.person_id == reading.device.person_id)
        about_location = rule.location_id == reading.location_id
        if about_them and about_location:
            hidden_people[person] = None

    return hidden_people


def get_current_readings_unhidden() -> PersonToReading:
    """
    Estimate a person's most mobile active device and its location by choosing one of several possible SensorReadings.
    """
    recent_readings = set(
        SensorReading.objects.select_related("device", "device__person", "location")
        .filter(created_at__gt=now() - timedelta(minutes=15))
        .order_by("created_at")
    )

    people = {x.device.person for x in recent_readings}
    locations = {x.location for x in recent_readings}
    rules = CustomThreshold.objects.filter(
        Q(Q(person__in=people) | Q(device__person__in=people)), location__in=locations, threshold__isnull=False
    ).select_related("device", "location", "device__person")
    custom_device_thresholds = {k: list(v) for k, v in groupby([x for x in rules if x.device], key=lambda x: x.device)}
    custom_person_thresholds = {k: list(v) for k, v in groupby([x for x in rules if x.person], key=lambda x: x.person)}

    over_threshold_readings = set()
    for reading in recent_readings:
        threshold = reading.location.threshold
        override_rules = custom_person_thresholds.get(reading.device.person, []) or custom_device_thresholds.get(
            reading.device, []
        )
        for rule in override_rules:
            if rule.location == reading.location and rule.threshold >= reading.rssi:
                threshold = rule.threshold

        if reading.rssi >= threshold:
            over_threshold_readings.add(reading)

    latest_device_readings = {x.device: x for x in over_threshold_readings}

    current_readings = {x: None for x in people}
    for person, readings in groupby(latest_device_readings.values(), key=lambda reading: reading.device.person):
        device_to_readings = {x.device: x for x in readings}
        best_device = get_most_mobile_device(device_to_readings.keys())
        best_reading = device_to_readings[best_device]
        current_readings[best_reading.device.person] = best_reading

    return current_readings


def get_current_positions():
    return (
        SensorReading.objects.filter(created_at__gt=now() - timedelta(minutes=15))
        .values("device__person__first_name", "device__person__last_name", "location_id")
        .annotate(updated_at=Max("created_at"))
    )


def get_never_detected() -> str:
    detected = set(SensorReading.objects.values_list("device__person_id", flat=True).distinct())
    people = set(Person.objects.values_list("id", flat=True).distinct())
    never_detected = people - detected
    return ", ".join(sorted([x.name for x in Person.objects.filter(id__in=never_detected)]))


@login_required
def index(request):
    user = request.user
    if not user.is_authenticated or not user.is_staff:
        return redirect(login)

    location_to_readings = {
        location: list(readings)
        for location, readings in groupby(get_current_readings().values(), key=lambda reading: reading.location)
    }
    return render(
        request, "index.html", {"location_to_readings": location_to_readings, "never_detected": get_never_detected()}
    )


def login(request):
    return render(request, "login.html")


def macs(request):
    return JsonResponse(
        {
            x["mac"]: x["person__first_name"] + " " + x["person__last_name"][0]
            for x in Device.objects.values("mac", "person__first_name", "person__last_name")
        }
    )


@csrf_exempt
@transaction.atomic
def scans(request):
    data = json.loads(request.body)
    location = data["location"]

    # Append scans to Positions table
    devices_by_mac = {x.mac: x.id for x in Device.objects.all()}
    locations_by_id = {x.clean_name(): x for x in Location.objects.all()}

    positions = [SensorReading(device=devices_by_mac[mac], location=locations_by_id[location]) for mac in data["macs"]]
    SensorReading.objects.bulk_create(positions)

    return HttpResponse(status=204)
