import warnings

from pandas.plotting import register_matplotlib_converters

from flock.algorithm import get_location_to_people

register_matplotlib_converters()

import matplotlib.pyplot as plt
import seaborn as sns
import subprocess
from datetime import timedelta
from typing import Dict
from typing import List
from typing import Tuple

from django.core.management.base import BaseCommand
from django.db.models import Max

from flock.models import CustomThreshold
from flock.models import Device
from flock.models import DeviceType
from flock.models import Location
from flock.models import Person
from flock.models import SensorReading


def above_thresholds(reading: SensorReading, location: Location, thresholds: List[CustomThreshold]):
    device_thresholds = [x for x in thresholds if x.device_id and x.device_id == reading.device_id]
    location_thresholds = [x for x in thresholds if reading.location_id == location.id]
    all_thresholds = [x.threshold for x in device_thresholds + location_thresholds + [location]]
    threshold = max(all_thresholds)
    return reading.rssi >= threshold


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-p", "--first_name")
        parser.add_argument("-n", "--num_hours", type=int)

    def handle(self, *args, **options):
        # options = {"first_name": "jason", "num_hours": 4}
        person = Person.objects.get(first_name__iexact=options["first_name"])
        num_hours = options["num_hours"]

        max_created_at = (
            SensorReading.objects.filter(device__person=person)
            .values("created_at")
            .aggregate(Max("created_at"))["created_at__max"]
        )
        xs = []
        ys = []
        colors = []
        sizes = []
        thresholds = CustomThreshold.objects.filter(person=person)

        all_recent_readings = (
            SensorReading.objects.all()
            .filter(device__person=person, created_at__gte=max_created_at - timedelta(hours=num_hours))
            .select_related("device", "person", "location")
        )

        location_devices = {(x.location, x.device) for x in all_recent_readings}
        sorted_location_devices = sorted(location_devices, key=lambda x: (x[0].id, x[1].device_type))
        y_to_location_devices: Dict[int, Tuple[Location, Device]] = dict(enumerate(sorted_location_devices))
        location_devices_to_y: Dict[Tuple[Location, Device], int] = {v: k for k, v in y_to_location_devices.items()}

        for x in all_recent_readings:
            print(x)

        for reading in all_recent_readings:
            xs.append(reading.created_at)
            ys.append(location_devices_to_y[(reading.location, reading.device)])
            if above_thresholds(reading, reading.location, thresholds):
                sizes.append(250)
            else:
                sizes.append(10)
            colors.append(reading.rssi)

        max_time = max(xs)
        min_time = min(xs) if min(xs) != max_time else max_time - timedelta(hours=1)

        with warnings.catch_warnings():
            # Bug in Pandas emits useless warning when sorting tz-aware index
            warnings.simplefilter("ignore")
            ax = sns.scatterplot(x=xs, y=ys, hue=colors, sizes=sizes, markers="o", legend="brief")

        labels = [
            f"{location.name}, {DeviceType.get(device.device_type).name.lower()}"
            for (location, device) in sorted_location_devices
        ]
        ax.yaxis.set_ticklabels(labels)
        ax.yaxis.set_ticks(sorted(set(ys)))
        ax.set_xlim(left=min_time, right=max_time)
        plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="right")

        print("\nestimates")
        current_time = min_time
        while current_time <= max_time:
            location_to_estimates = get_location_to_people(current_time)
            for location, estimates in location_to_estimates.items():
                people_to_estimates = {x.person: x for x in estimates}
                if person not in people_to_estimates:
                    continue
                estimate = people_to_estimates[person]
                if estimate:
                    print(estimate)

            current_time += timedelta(minutes=1)
            # reading = readings_unhidden.get(person)
            # if reading:
            #     if person in overrides:
            #         color = "red"
            #     else:
            #         color = created_at_color(reading.created_at, current_time)
            #     ax.hlines(
            #         y=location_devices_to_y[(reading.location, reading.device)],
            #         xmin=current_time,
            #         xmax=current_time + timedelta(minutes=1),
            #         color=color,
            #         zorder=1,
            #     )
            #     # print("YUP ", current_time, readings_unhidden[person], color)
            # else:
            #     pass
            #     #     print("NOPE", current_time)

        plt.tight_layout()
        plt.title(person.name)

        filename = f"/tmp/plot_person_{person.first_name.lower()}.png"
        plt.savefig(filename)
        subprocess.call(["open", filename])
