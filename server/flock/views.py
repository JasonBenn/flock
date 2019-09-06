import json
from collections import defaultdict

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from flock.models import Device
from flock.models import Person


def index(request):
    people_by_location = defaultdict(list)
    for person in Person.objects.filter(location__isnull=False):
        people_by_location[person.location].append(person.name)

    return render(request, "index.html", {"people_by_location": dict(people_by_location)})


def macs(request):
    return JsonResponse({"macs": [x.mac for x in Device.objects.all()]})


@csrf_exempt
def scans(request):
    return JsonResponse(json.loads(request.body))
