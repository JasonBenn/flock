import re

from django.contrib.postgres.indexes import BrinIndex
from django.db import models
from django.db.models import DateTimeField
from stringcase import camelcase
from stringcase import snakecase

from .utils import now


class Location(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)

    def __str__(self):
        return self.name

    def clean_name(self):
        return snakecase( re.sub("[^\w ]+", "", self.name.replace("/", " ")).lower())

    def snake_case_name(self):
        return self.clean_name()

    def camel_case_name(self):
        return camelcase(self.clean_name())


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


class Device(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, help_text="<p>Short description of this device (e.g. laptop, phone)</p>")
    mac = models.CharField(max_length=17, unique=True, help_text="<p>Format: <code>AA:BB:CC:DD:00:11</code></p>"
                                                                 "<p>How to find your Bluetooth mac address on various devices:</p>"
                                                                 "<p><strong>iPhone</strong>: Settings -> General -> About -> Bluetooth</p>"
                                                                 "<p><strong>Android</strong>: varies. Sometimes in the Bluetooth pairing menu, sometimes in About Phone</p>"
                                                                 "<p><strong>Mac</strong> (heh): Preferences -> Bluetooth -> Show Bluetooth in menu bar; then option-click on the Bluetooth icon -> Address</p>"
                           )

    def __str__(self):
        return f"{self.person}'s {self.name} ({self.mac})"


class Position(models.Model):
    person = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    location = models.ForeignKey(Location, on_delete=models.DO_NOTHING)
    created_at = DateTimeField(default=now)

    class Meta:
        indexes = [BrinIndex(fields=["created_at"])]

    def __str__(self):
        return f"person {self.person_id} @ location {self.location_id}, {self.created_at.strftime('%X %p')}"
