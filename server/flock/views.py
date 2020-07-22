import json
from datetime import datetime

import pytz
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from flock.algorithm import get_chore_leaderboard
from flock.algorithm import get_location_to_people, get_stubbed_location_to_people, quiet_locations
from flock.models import ChoreAction
from flock.models import Device
from flock.models import GroundTruth
from flock.models import Location
from flock.models import Person
from flock.models import SensorReading


def get_homepage_context_data():
    return {"location_to_people": get_location_to_people(), "quiet_locations": quiet_locations()}


@login_required
def index(request):
    user = request.user
    if not user.is_authenticated or not user.is_staff:
        return redirect(login)

    return render(request, "index.html", get_homepage_context_data())


@login_required
def get_contents(request):
    user = request.user
    if not user.is_authenticated or not user.is_staff:
        return redirect(login)

    return render(request, "contents.html", get_homepage_context_data())


def chore_leaderboard(request):
    print({"people_chores": get_chore_leaderboard()})
    return render(request, "chore_leaderboard.html", {"floors_people_chores": get_chore_leaderboard()})


@login_required
def report_chore(request):
    person = Person.objects.get(email=request.user.email)
    ChoreAction.objects.create(person=person, chore=request.GET.get('name'), minutes=request.GET.get('mins'))
    return render(request, "chore_leaderboard.html", {"floors_people_chores": get_chore_leaderboard()})


@login_required
def report_ground_truth(request):
    return render(
        request,
        "report_ground_truth.html",
        {
            "people": [{"name": x.name, "id": x.id} for x in Person.objects.all().order_by("first_name")],
            "locations": Location.objects.all().order_by("name"),
            "current_location_id": (int(request.GET.get("location_id", -1))),
        },
    )


def thanks(request):
    return render(request, "thanks.html")


def post_ground_truths(request):
    location_id = request.POST.get("location_id")
    present_person_ids = request.POST.getlist("present_person_id")
    not_present_person_ids = request.POST.getlist("not_present_person_id")
    for person_id in present_person_ids:
        GroundTruth.objects.create(person_id=person_id, location_id=location_id, present=True)
    for person_id in not_present_person_ids:
        GroundTruth.objects.create(person_id=person_id, location_id=location_id, present=False)
    return HttpResponseRedirect("/thanks")


def login(request):
    return render(request, "login.html")


def macs(request):
    return JsonResponse(
        {x.mac: x.person.name for x in Device.objects.filter(active=True, person__active=True).select_related("person").order_by("device_type", "mac")}
    )


@csrf_exempt
@transaction.atomic
def scans(request):
    data = json.loads(request.body)
    location = data["location"]

    # Append scans to Positions table
    device_ids_by_mac = {x.mac: x.id for x in Device.objects.all()}
    locations_by_id = {x.clean_name(): x for x in Location.objects.all()}

    for scan_result in data["scan_results"]:
        SensorReading.objects.create(
            device_id=device_ids_by_mac[scan_result["mac"]],
            location=locations_by_id[location],
            rssi=scan_result["rssi"],
            created_at=scan_result["scanned_at"],
        )

    return HttpResponse(status=204)


def stubbed_data(request):
    num_locations = request.GET["num_locations"] and int(request.GET["num_locations"])
    return render(request, "index.html", {"location_to_people": get_stubbed_location_to_people(num_locations)})
