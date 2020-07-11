import re

import pytz
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import BrinIndex
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import BooleanField, DateTimeField, IntegerField
from django.db.models import ForeignKey
from django.db.models import TextField
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django_enumfield.db.fields import EnumField
from django_enumfield.enum import Enum

from flock.utils import friendly_time, now


class TZAwareDateTimeField(models.DateTimeField):
    def from_db_value(self, value, expression, connection, context):
        if value is None:
            return None
        else:
            return value.replace(tzinfo=pytz.UTC)


class Location(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    threshold = models.IntegerField(default=-10)
    active = BooleanField(default=True)

    def __str__(self):
        return self.name

    def clean_name(self):
        return re.sub(r"[^\w ]+", "", self.name.replace("/", " ")).lower().replace(" ", "_")


class Person(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    active = BooleanField(default=True)

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


def mac_validator(mac):
    if not re.search(r"[A-Z0-9]{2}:[A-Z0-9]{2}:[A-Z0-9]{2}:[A-Z0-9]{2}:[A-Z0-9]{2}:[A-Z0-9]{2}", mac):
        raise ValidationError("MAC address should be formatted AA:BB:CC:DD:00:11")


class Device(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    device_type = EnumField(DeviceType)
    created_at = DateTimeField(default=now, editable=False)
    active = BooleanField(default=True)
    mac = models.CharField(
        max_length=17,
        unique=True,
        validators=[mac_validator],
        help_text="<p>Format: <code>AA:BB:CC:DD:00:11</code></p>"
        "<p>How to find your Bluetooth mac address on various devices:</p>"
        "<p><strong>iPhone</strong>: Settings -> General -> About -> Bluetooth</p>"
        "<p><strong>Android</strong>: varies. Sometimes in the Bluetooth pairing menu, sometimes in About Phone</p>"
        "<p><strong>Mac</strong>: Preferences -> Bluetooth -> Show Bluetooth in menu bar; then option-click on the Bluetooth icon -> Address</p>"
        "<p><strong>Windows</strong>: Command Prompt -> enter <code>ipconfig /all</code> -> Physical address (MAC)</p>",
    )

    def __str__(self):
        return f"{self.person}'s {DeviceType.get(self.device_type)} ({self.mac})"


class Estimate(models.Model):
    class Meta:
        abstract = True
        indexes = [BrinIndex(fields=["created_at"])]

    person = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    location = models.ForeignKey(Location, on_delete=models.DO_NOTHING)
    present = BooleanField(default=True)
    created_at = DateTimeField(default=now)


class SensorReading(Estimate):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    rssi = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{friendly_time(self.created_at)}: {self.rssi or '':>3} @ {self.location.name[:10]:<11} {self.device.person.name}'s {DeviceType.get(self.device.device_type)}"


@receiver(pre_save, sender=SensorReading)
def backfill_fields(sender, instance, **kwargs):
    instance.person_id = instance.device.person_id
    instance.present = instance.rssi is not None


class GroundTruth(Estimate):
    device = models.ForeignKey(
        Device, on_delete=models.DO_NOTHING, null=True, blank=True, help_text="Helpful, but optional."
    )
    fixed_at = DateTimeField(blank=True, null=True)

    def __str__(self):
        present_str = "@" if self.present else "!@"
        return f"{friendly_time(self.created_at)}: {self.person.name} {present_str} {self.location.name}"


def custom_threshold_validator(threshold):
    if threshold > 5 and not threshold == 100:
        raise ValidationError(
            "If you're going to set the threshold so high as to avoid detection altogether, it must be exactly 100."
        )


class CustomThreshold(models.Model):
    person = ForeignKey(
        Person,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Optional. Set a custom threshold for all this person's devices at Location. Don't fill this in if you set Device, which is more specific.",
    )
    device = ForeignKey(
        Device,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text="Optional. Set a custom threshold for this Device at Location. Don't fill in if you set a Person.",
    )
    location = ForeignKey(Location, null=True, blank=True, on_delete=models.SET_NULL, help_text="Optional.")
    threshold = models.IntegerField(
        default=-5,
        validators=[custom_threshold_validator],
        help_text="<p>Enter a threshold that must be exceeded for detection.</p>"
        "<p>The quietest/most distant reading I've ever seen is -35 dB.</p>"
        "<p>Devices in the same room range from -10 (the default threshold) to 0.</p>"
        "<p>The loudest/closest reading I've ever seen is 5 dB.</p>"
        "<p><strong>To require a device/person be really close to a location</strong>: enter -5.</p>"
        "<p><strong>To hide a device/person from a location</strong>: enter 100.</p>",
    )
    reason = TextField(null=True, blank=True)

    def __str__(self):
        components = [str(self.threshold)]
        if self.person:
            components.append(self.person.first_name)
        if self.location:
            components.append(self.location.name)
        if self.device:
            components.append(DeviceType.get(self.device.device_type).name)
        return ", ".join([x for x in components if x])


class ChillTimesThreshold(models.Model):
    threshold = models.IntegerField(
        default=5,
        help_text="<p>The first time this many people are detected (>=) that day, post to Slack.</p>")
    location = models.ForeignKey(Location, on_delete=models.DO_NOTHING)
    created_at = DateTimeField(default=now)

    def __str__(self):
        return f"ChillTimesThreshold: {self.location} >= {self.threshold}"


class ChillTime(models.Model):
    person_ids = ArrayField(IntegerField())
    location = models.ForeignKey(Location, on_delete=models.DO_NOTHING)
    created_at = DateTimeField(default=now)

    def __str__(self):
        people = Person.objects.filter(id__in=self.person_ids)
        return f"{', '.join([x.name for x in people])} in {self.location} at {friendly_time(self.created_at)}"
