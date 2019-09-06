from collections import defaultdict

from django.shortcuts import render

from flock.models import Person


def index(request):
    people_by_location = defaultdict(list)
    for person in Person.objects.filter(location__isnull=False):
        people_by_location[person.location].append(person.name)

    return render(request, "index.html", {"people_by_location": dict(people_by_location)})
