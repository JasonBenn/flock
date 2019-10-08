import subprocess
from datetime import timedelta
from typing import Dict
from typing import List

import numpy as np
from django.core.management.base import BaseCommand
from django.db.models import Max
from django.utils.timezone import localtime

from flock.models import CustomThreshold
from flock.models import Device
from flock.models import DeviceType
from flock.models import Location
from flock.models import Person
from flock.models import SensorReading
from flock.templatetags.template_utils import created_at_color
from flock.views import get_current_readings_unhidden
from flock.views import get_matching_override_rules


def above_thresholds(reading: SensorReading, location: Location, thresholds: List[CustomThreshold]):
    device_thresholds = [x for x in thresholds if x.device_id and x.device_id == reading.device_id]
    location_thresholds = [x for x in thresholds if reading.location_id == location.id]
    all_thresholds = [x.threshold for x in device_thresholds + location_thresholds + [location]]
    threshold = max(all_thresholds)
    return reading.rssi >= threshold


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-n", "--first_name")

    def handle(self, *args, **options):
        person = Person.objects.get(first_name__iexact=options["first_name"])

        max_created_at = (
            SensorReading.objects.filter(device__person=person)
            .values("created_at")
            .aggregate(Max("created_at"))["created_at__max"]
        )
        xs = []
        location_devices = []
        colors = []
        sizes = []
        num_hours = 5

        DeviceID = int
        detected = set(SensorReading.objects.values_list("device", flat=True).distinct())

        thresholds = CustomThreshold.objects.filter(person=person)

        y_ids: Dict[DeviceID, int] = {v: k for k, v in enumerate(detected)}
        all_recent_readings = (
            SensorReading.objects.all()
            .filter(device__person=person, created_at__gte=max_created_at - timedelta(hours=num_hours))
            .select_related("device", "device__person", "location")
        )

        for reading in all_recent_readings:
            xs.append(localtime(reading.created_at))
            location_devices.append((reading.location, reading.device))
            if above_thresholds(reading, reading.location, thresholds):
                sizes.append(50)
            else:
                sizes.append(10)
            colors.append(reading.rssi)

        ordered_location_devices = sorted(enumerate(set(location_devices)))
        location_device_to_y = {v: k for k, v in ordered_location_devices}

        ys = [location_device_to_y[location_device] for location_device in location_devices]

        device_names: Dict[int, str] = {}
        for device in Device.objects.all().order_by("id").filter(id__in=detected):
            device_names[y_ids[device.id]] = f"{device.person} {DeviceType.get(device.device_type)}"

        min_time = min(xs)
        max_time = max(xs)

        import matplotlib.pyplot as plt

        plt.clf()
        fig, ax1 = plt.subplots(figsize=(num_hours * 3, 3))
        ax1.legend(colors)
        scatter = ax1.scatter(x=xs, y=ys, c=colors, s=sizes, marker="o", zorder=3)
        ax1.legend(*scatter.legend_elements(), loc="center left", title="RSSI", bbox_to_anchor=(1.05, 0.5))
        ax1.set_xlim(left=min_time, right=max_time)
        labels = [
            f"{location.name} {DeviceType.get(device.device_type)}"
            for index, (location, device) in reversed(ordered_location_devices)
        ]
        ax1.yaxis.set_ticklabels(labels)
        ax1.yaxis.set_ticks(sorted(set(ys)))

        data = [np.arange(len(xs))]

        current_time = min_time
        while current_time <= max_time:
            readings_unhidden = get_current_readings_unhidden(at_time=current_time)
            overrides = get_matching_override_rules(readings_unhidden)
            reading = readings_unhidden.get(person)
            if reading:
                if person in overrides:
                    color = "red"
                else:
                    color = created_at_color(reading.created_at, current_time)
                ax1.hlines(
                    y=location_device_to_y[(reading.location, reading.device)],
                    xmin=current_time,
                    xmax=current_time + timedelta(minutes=1),
                    color=color,
                    zorder=1,
                )
                # print("YUP ", current_time, readings_unhidden[person], color)
            else:
                pass
                #     print("NOPE", current_time)
            current_time += timedelta(minutes=1)

        plt.setp(ax1.get_xticklabels(), rotation=30, horizontalalignment="right")

        plt.tight_layout()
        plt.title(person.name)

        filename = f"/tmp/plot_person_{person.first_name.lower()}.png"
        plt.savefig(filename)
        subprocess.call(["open", filename])

        # BUG: y labels are wrong
