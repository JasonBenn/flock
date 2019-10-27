from datetime import timedelta

from django.core.management.base import BaseCommand

from flock.models import Location
from flock.models import SensorReading
from flock.utils import now


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("-n", "--name")

    def handle(self, *args, **options):
        location = Location.objects.get(name__icontains=options["name"])
        for reading in SensorReading.objects.filter(location=location, created_at__gte=now() - timedelta(hours=2)):
            print(reading)

        # xs = []
        # ys = []
        # colors = []
        # # Create DataFrame with x, y, color columns.
        # detected = set(SensorReading.objects.values_list("device", flat=True).distinct())
        # y_ids = {v: k for k, v in enumerate(detected)}
        # for reading in SensorReading.objects.all().filter(
        #     location=location, created_at__gte=max_created_at - timedelta(minutes=90)
        # ):
        #     xs.append(reading.created_at)
        #     ys.append(y_ids[reading.device_id])
        #     colors.append(reading.rssi)
        #
        # device_names = {}
        # for device in Device.objects.all().order_by("id").filter(id__in=detected):
        #     device_names[y_ids[device.id]] = f"{device.person} {DeviceType.get(device.device_type)}"
        #
        # # df = DataFrame({"x": xs, "y": ys, "color": colors})
        # import matplotlib.pyplot as plt
        #
        # plt.clf()
        # fig, axs = plt.subplots(1, 1)
        # plt.title(location.name)
        # # plt.colorbar(colors)
        # axs.scatter(x=xs, y=ys, c=colors)
        # axs.set_yticklabels(device_names.values())
        # plt.tight_layout()
        # plt.savefig(f"/tmp/plot_location_{location.clean_name()}.png")
        # print(device_names)
