import re

from django.contrib.postgres.indexes import BrinIndex
from django.db import models
from django.db.models import DateTimeField
from django.db.models import ForeignKey
from django_enumfield.db.fields import EnumField
from django_enumfield.enum import Enum

from .utils import now


class Location(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    threshold = models.IntegerField(default=-10)

    def __str__(self):
        return self.name

    def clean_name(self):
        return re.sub(r"[^\w ]+", "", self.name.replace("/", " ")).lower().replace(" ", "_")


class Person(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)

    class Meta:
        unique_together = ("first_name", "last_name")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def name(self):
        return f"{self.first_name} {self.last_name[0]}"


class DeviceType(Enum):
    WEARABLE = 1
    PHONE = 2
    LAPTOP = 3
    WORK_LAPTOP = 4
    TABLET = 5
    OTHER = 6


class Device(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=200,
        help_text="<p>Short description of this device (e.g. laptop, phone)</p>"
        "<p>Add each device that you might carry with you!</p>",
        null=True,
        blank=True,
    )
    device_type = EnumField(DeviceType)
    mac = models.CharField(
        max_length=17,
        unique=True,
        help_text="<p>Format: <code>AA:BB:CC:DD:00:11</code></p>"
        "<p>How to find your Bluetooth mac address on various devices:</p>"
        "<p><strong>iPhone</strong>: Settings -> General -> About -> Bluetooth</p>"
        "<p><strong>Android</strong>: varies. Sometimes in the Bluetooth pairing menu, sometimes in About Phone</p>"
        "<p><strong>Mac</strong> (heh): Preferences -> Bluetooth -> Show Bluetooth in menu bar; then option-click on the Bluetooth icon -> Address</p>",
    )

    def __str__(self):
        return f"{self.person}'s {DeviceType.get(self.device_type)} ({self.mac})"


class SensorReading(models.Model):
    device = models.ForeignKey(Device, on_delete=models.DO_NOTHING)
    location = models.ForeignKey(Location, on_delete=models.DO_NOTHING)
    rssi = models.IntegerField()
    created_at = DateTimeField(default=now)

    class Meta:
        indexes = [BrinIndex(fields=["created_at"])]

    def __str__(self):
        # return f"person {self.device_id} @ location {self.location_id}, {self.created_at.strftime('%X %p')}"
        return f"{self.rssi}: {self.device.person.first_name}'s' {DeviceType.get(self.device.device_type)} @ {self.location.name}, {self.created_at.strftime('%X %p')}"


class OverrideRule(models.Model):
    person = ForeignKey(Person, null=True, on_delete=models.SET_NULL, help_text="Optional.")
    location = ForeignKey(Location, null=True, on_delete=models.SET_NULL, help_text="Optional.")
    device = ForeignKey(Device, null=True, on_delete=models.SET_NULL, help_text="Optional.")
    custom_threshold = models.IntegerField(
        default=-5,
        null=True,
        help_text="Enter a threshold that must be exceeded for detection. If you never want a person/location/device "
        "combination to be detected, enter 100.",
    )

    def __str__(self):
        # return f"person {self.device_id} @ location {self.location_id}, {self.created_at.strftime('%X %p')}"
        components = [str(self.custom_threshold)]
        if self.person:
            components.append(self.person.first_name)
        if self.location:
            components.append(self.location.name)
        if self.device:
            components.append(DeviceType.get(self.device.device_type))
        return ", ".join([x for x in components if x])
