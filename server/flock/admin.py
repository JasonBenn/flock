from django.contrib import admin
from django.contrib.auth.models import Group

from flock.models import Device, Location, Person, SensorReading
from flock.models import CustomThreshold


class LocationAdmin(admin.ModelAdmin):
    ordering = ("name",)


admin.site.register(Location, LocationAdmin)


class PersonAdmin(admin.ModelAdmin):
    ordering = ("first_name",)


admin.site.register(Person, PersonAdmin)


class DeviceAdmin(admin.ModelAdmin):
    ordering = ("person__first_name",)


class CustomThresholdsAdmin(admin.ModelAdmin):
    """
    Add your other customizations
    like actions, list_display, list filter, etc
    """

    ordering = ("person__first_name",)
    list_display = ["person", "location", "device", "threshold", "reason"]


admin.site.register(Device, DeviceAdmin)
admin.site.register(CustomThreshold, CustomThresholdsAdmin)
admin.site.register(SensorReading)

admin.site.unregister(Group)
