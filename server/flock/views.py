import json
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from itertools import groupby
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Max
from django.db.models import Q
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.timezone import localtime
from django.views.decorators.csrf import csrf_exempt

from flock.models import CustomThreshold
from flock.models import Device
from flock.models import GroundTruth
from flock.models import Location
from flock.models import Person
from flock.models import SensorReading

MAX_THRESHOLD = 100

PersonToReading = Dict[Person, Optional[SensorReading]]
PersonToEstimate = Dict[Person, Optional[Union[SensorReading, GroundTruth]]]


def get_most_mobile_device(devices):
    return sorted(devices, key=lambda x: x.device_type)[0]


def get_current_readings(at_time: Optional[datetime] = None) -> PersonToReading:
    at_time = get_at_time(at_time)
    current_readings_unhidden = get_current_readings_unhidden(at_time)
    overrides = get_matching_override_rules(current_readings_unhidden)
    return {**current_readings_unhidden, **overrides}


def get_at_time(at_time):
    if at_time is None and settings.FREEZE_TIME:
        at_time = SensorReading.objects.aggregate(Max('created_at'))['created_at__max']
    return at_time


def get_matching_override_rules(person_readings: PersonToReading) -> PersonToReading:
    """
    Identifies the people whose location estimate should be hidden.
    Given a list of PersonToReading, return a subset that maps those people to None.
    """
    locations = [reading.location for person, reading in person_readings.items() if reading]
    custom_thresholds = CustomThreshold.objects.filter(
        Q(Q(person__in=person_readings.keys()) | Q(device__person__in=person_readings.keys())), location__in=locations
    ).select_related("device", "device__person")

    hidden_people = {}
    for rule in custom_thresholds:
        person = rule.person or (rule.device and rule.device.person)
        reading = person_readings.get(person)
        if not reading:
            continue
        about_them = (rule.device_id == reading.device_id) or (rule.person_id == reading.device.person_id)
        about_location = rule.location_id == reading.location_id
        if about_them and about_location and reading.rssi < rule.threshold:
            hidden_people[person] = None

    return hidden_people


def get_current_readings_unhidden(at_time: Optional[datetime] = None) -> PersonToReading:
    """
    Estimate a person's most mobile active device and its location by choosing one of several possible SensorReadings.
    """
    at_time = get_at_time(at_time)
    recent_readings = list(
        SensorReading.objects.select_related("device", "device__person", "location")
        .filter(created_at__gt=at_time - timedelta(minutes=15), created_at__lte=at_time)
        .order_by("-created_at")
    )

    people = {x.device.person for x in recent_readings}
    locations = {x.location for x in recent_readings}
    rules = (
        CustomThreshold.objects.filter(
            Q(Q(person__in=people) | Q(device__person__in=people)), location__in=locations, threshold__isnull=False
        )
        .exclude(threshold=100)
        .select_related("device", "location", "device__person")
    )
    custom_device_thresholds = {k: list(v) for k, v in groupby([x for x in rules if x.device], key=lambda x: x.device)}
    custom_person_thresholds = {k: list(v) for k, v in groupby([x for x in rules if x.person], key=lambda x: x.person)}
    over_threshold_readings = set()
    for reading in recent_readings:
        threshold = reading.location.threshold
        custom_thresholds = custom_person_thresholds.get(reading.device.person, []) or custom_device_thresholds.get(
            reading.device, []
        )
        for rule in custom_thresholds:
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
        SensorReading.objects.filter(created_at__gt=localtime() - timedelta(minutes=15))
        .values("device__person__first_name", "device__person__last_name", "location_id")
        .annotate(updated_at=Max("created_at"))
    )


@login_required
def index(request):
    user = request.user
    if not user.is_authenticated or not user.is_staff:
        return redirect(login)

    context = _get_main_contents_context()
    return render(request, "index.html", context)


@login_required
def get_contents(request):
    user = request.user
    if not user.is_authenticated or not user.is_staff:
        return redirect(login)

    context = _get_main_contents_context()
    return render(request, "contents.html", context)


@login_required
def report_ground_truth(request):
    current_readings = get_current_readings()
    return render(
        request,
        "report_ground_truth.html",
        {
            "people": [
                {"name": x.name, "id": x.id, "present": current_readings.get(x)}
                for x in Person.objects.all().order_by("first_name")
            ],
            "locations": Location.objects.all().order_by("name"),
            "current_location_id": (int(request.GET.get('location_id', -1)))
        },
    )


def thanks(request):
    return render(request, 'thanks.html')


def post_ground_truths(request):
    location_id = request.POST.get('location_id')
    present_person_ids = request.POST.getlist('present_person_id')
    not_present_person_ids = request.POST.getlist('not_present_person_id')
    for person_id in present_person_ids:
        GroundTruth.objects.create(person_id=person_id, location_id=location_id, present=True)
    for person_id in not_present_person_ids:
        GroundTruth.objects.create(person_id=person_id, location_id=location_id, present=False)
    return HttpResponseRedirect('/thanks')


def merge_recent_ground_truths(current_readings: PersonToReading, at_time: Optional[datetime] = None) -> PersonToEstimate:
    at_time = get_at_time(at_time)
    ground_truths = GroundTruth.objects.filter(created_at__gte=at_time - timedelta(minutes=15))#, created_at__lte=at_time)  TODO
    ground_truths_by_people = {x.person: x for x in ground_truths}

    person_estimates: PersonToEstimate = current_readings.copy()
    for person, reading in current_readings.items():
        truth = ground_truths_by_people.get(person)
        if reading and truth and reading.location != truth.location:
            person_estimates[person] = truth
    return person_estimates


def _get_main_contents_context():
    location_to_estimates = defaultdict(list)
    current_readings = get_current_readings()
    person_estimates = merge_recent_ground_truths(current_readings)
    for estimate in person_estimates.values():
        if estimate:
            location_to_estimates[estimate.location].append(estimate)

    context = {"location_to_estimates": dict(location_to_estimates)}
    return context


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
    device_ids_by_mac = {x.mac: x.id for x in Device.objects.all()}
    locations_by_id = {x.clean_name(): x for x in Location.objects.all()}

    positions = [
        SensorReading(device_id=device_ids_by_mac[mac], location=locations_by_id[location], rssi=rssi)
        for mac, rssi in data["macs"].items()
    ]
    SensorReading.objects.bulk_create(positions)

    return HttpResponse(status=204)
