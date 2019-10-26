from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from functools import partial
from operator import attrgetter
from operator import itemgetter
from statistics import StatisticsError
from statistics import mean
from statistics import mode
from typing import Dict
from typing import List
from typing import Optional

from django.contrib.admin.utils import flatten
from django.utils.functional import partition

from flock.constants import MAX_THRESHOLD
from flock.constants import READING_WINDOW_MINUTES
from flock.models import CustomThreshold
from flock.models import Estimate
from flock.models import GroundTruth
from flock.models import Location
from flock.models import Person
from flock.models import SensorReading
from flock.utils import get_at_time
from flock.utils import group_by


def get_recent_estimates_by_type(at_time: Optional[datetime] = None) -> Dict[Person, Dict[str, List[Estimate]]]:
    at_time = get_at_time(at_time)
    all_people = {person: {} for person in Person.objects.all()}

    recent_truths = GroundTruth.objects.filter(
        created_at__gte=at_time - timedelta(minutes=READING_WINDOW_MINUTES), created_at__lt=at_time
    ).select_related("person", "location")
    for person, truths in group_by(recent_truths, key=attrgetter("person")).items():
        all_people[person]["truths"] = truths

    recent_readings = SensorReading.objects.filter(
        created_at__gte=at_time - timedelta(minutes=READING_WINDOW_MINUTES), created_at__lt=at_time
    ).select_related("person", "location")
    for person, readings in group_by(recent_readings, key=attrgetter("person")).items():
        all_people[person]["readings"] = readings

    return {person: objects for person, objects in all_people.items() if len(objects)}


def get_valid_estimates(estimates_by_type: Dict[Person, Dict[str, List[Estimate]]]) -> Dict[Person, List[Estimate]]:
    custom_thresholds: Dict[Person, Dict[Location, int]] = {x: {} for x in Person.objects.all()}
    for threshold in CustomThreshold.objects.exclude(threshold=MAX_THRESHOLD).select_related("person", "location"):
        person = threshold.person or threshold.device.person
        custom_thresholds[person][threshold.location] = threshold.threshold

    valid_estimates = {}
    for person, estimates in estimates_by_type.items():
        invalid_readings, valid_readings = partition(
            partial(_is_valid, custom_thresholds), estimates.get("readings", [])
        )
        valid_estimates[person] = sorted(
            estimates_by_type[person].get("truths", []) + valid_readings, key=attrgetter("created_at")
        )
    return valid_estimates


def get_people_to_location(all_valid_estimates: Dict[Person, List[Estimate]]):
    people_to_location: Dict[Person, Location] = {}
    for person, person_estimates in all_valid_estimates.items():
        if not len(person_estimates):
            continue

        # If most recent overall estimate is a positive GroundTruth, return that.
        most_recent_estimate = person_estimates[-1]
        if isinstance(most_recent_estimate, GroundTruth) and most_recent_estimate.present:
            people_to_location[person] = most_recent_estimate.location
            continue

        # If there aren't any SensorReadings, return nothing
        if not len([x for x in person_estimates if isinstance(x, SensorReading)]):
            continue

        # Group estimates by location
        location_to_estimates = group_by(person_estimates, key=attrgetter("location"))
        # (except locations that were most recently labeled as not present)
        location_to_estimates = {k: v for k, v in location_to_estimates.items() if v[-1].present}

        # First test: if a location has recently experienced a clearly higher RSSI than others, return that.
        high_rssi_locations = best_locations_by_rssi(location_to_estimates)
        if len(high_rssi_locations) == 1:
            people_to_location[person] = high_rssi_locations[0]
        high_rssi_location_to_estimates = {k: v for k, v in location_to_estimates.items() if k in high_rssi_locations}

        # Otherwise, if one high RSSI locations is meaningfully more recent, than return that.
        recent_locations = best_locations_by_recency(high_rssi_location_to_estimates)
        if len(recent_locations) == 1:
            people_to_location[person] = recent_locations[0]
        recent_location_to_estimates = {
            k: v for k, v in high_rssi_location_to_estimates.items() if k in recent_locations
        }

        # If there are still multiple contenders, try to classify each device and prefer the more mobile one.
        most_mobile_location = best_locations_by_device_mobility(recent_location_to_estimates)
        if most_mobile_location:
            people_to_location[person] = most_mobile_location

        # What about grouping estimates by device? How would that work?
        # Probably would want each device to get classified.

    return people_to_location


def best_locations_by_rssi(location_to_estimates: Dict[Location, List[Estimate]]) -> List[Location]:
    location_to_readings = {
        location: [x for x in estimates if isinstance(x, SensorReading)]
        for location, estimates in location_to_estimates.items()
    }
    location_to_average_rssi = {
        location: mean([x.rssi for x in estimates]) for location, estimates in location_to_readings.items()
    }

    highest_overall_rssi = max(flatten(location_to_average_rssi.values()))
    best_locations = [
        location
        for location, average_rssi in location_to_average_rssi.items()
        if abs(average_rssi - highest_overall_rssi) <= 5
    ]
    return best_locations


def best_locations_by_recency(location_to_estimates: Dict[Location, List[Estimate]]) -> List[Location]:
    max_created_at = max(flatten(location_to_estimates.values()), key=lambda x: x.created_at)
    best_locations = [
        location
        for location, estimates in location_to_estimates.items()
        if (max_created_at.created_at - estimates[-1].created_at) <= timedelta(minutes=5)
    ]
    return best_locations


def best_locations_by_device_mobility(location_to_estimates: Dict[Location, List[Estimate]]) -> Location:
    best_location, _ = max(location_to_estimates.items(), key=lambda x: x[1][-1].device.device_type)
    return best_location


def _is_valid(custom_thresholds: Dict[Person, Dict[Location, int]], reading: SensorReading) -> bool:
    return reading.rssi >= max(
        [reading.location.threshold, custom_thresholds[reading.person].get(reading.location, float("-inf"))]
    )


def mask_people_to_location(people_to_location: Dict[Person, Location]) -> Dict[Person, Location]:
    person_ids = CustomThreshold.objects.filter(
        person__in=list(people_to_location.keys()), threshold=MAX_THRESHOLD
    ).values_list("person_id", flat=True)
    return {k: v for k, v in people_to_location.items() if k.id not in person_ids}


def get_location_to_people(
    at_time: Optional[datetime] = None, exclude_ground_truths=False
) -> Dict[Location, List[Person]]:
    recent_estimates_by_type = get_recent_estimates_by_type(at_time)
    if exclude_ground_truths:
        recent_estimates_by_type = {
            person: {"readings": estimates_dict.get("readings", [])}
            for person, estimates_dict in recent_estimates_by_type.items()
        }
    valid_estimates = get_valid_estimates(recent_estimates_by_type)
    people_to_location = get_people_to_location(valid_estimates)
    masked_people_to_location = mask_people_to_location(people_to_location)
    location_to_people = defaultdict(list)
    for person, location in masked_people_to_location.items():
        location_to_people[location].append(person)
    return dict(location_to_people)


def get_most_mobile_device(devices):
    return sorted(devices, key=lambda x: x.device_type)[0]
