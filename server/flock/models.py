from django.contrib.postgres.indexes import BrinIndex
from django.db import models
from django.db.models import DateTimeField

from .utils import now


class Location(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Person(models.Model):
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    location = models.ForeignKey(Location, null=True, on_delete=models.SET_NULL)

    class Meta:
        unique_together = ("first_name", "last_name")

    def __str__(self):
        return f"{self.first_name} {self.last_name} {self.location}"

    @property
    def name(self):
        return f"{self.first_name} {self.last_name[0]}"


class Device(models.Model):
    mac = models.CharField(max_length=17, unique=True)  # 00:00:00:00:00:00
    name = models.CharField(max_length=200)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.mac} {self.person}"


class Position(models.Model):
    person = models.ForeignKey(Person, on_delete=models.DO_NOTHING)
    location = models.ForeignKey(Location, on_delete=models.DO_NOTHING)
    created_at = DateTimeField(default=now)

    class Meta:
        indexes = [BrinIndex(fields=["created_at"])]
