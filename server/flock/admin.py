from django.contrib import admin
from django.contrib.auth.models import Group

from flock.models import CustomThreshold
from flock.models import Device
from flock.models import GroundTruth
from flock.models import Location
from flock.models import Person
from flock.models import SensorReading


class LocationAdmin(admin.ModelAdmin):
    ordering = ("name",)


admin.site.register(Location, LocationAdmin)


class PersonAdmin(admin.ModelAdmin):
    ordering = ("first_name",)


admin.site.register(Person, PersonAdmin)


class DeviceAdmin(admin.ModelAdmin):
    ordering = ("person__first_name",)


class CustomThresholdAdmin(admin.ModelAdmin):
    ordering = ("person__first_name",)
    list_display = ["person", "location", "device", "threshold", "reason"]


admin.site.register(Device, DeviceAdmin)
admin.site.register(CustomThreshold, CustomThresholdAdmin)


def rssi_to_ten(modeladmin, request, queryset):
    for reading in queryset:
        reading.rssi = 10
        reading.save()


rssi_to_ten.short_description = "Change RSSI to 10"


class SensorReadingAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ["device", "location", "rssi", "created_at"]
    exclude = ("person", "present")
    actions = [rssi_to_ten]  # <-- Add the list action function here


admin.site.register(SensorReading, SensorReadingAdmin)


class GroundTruthAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ["person", "location", "present", "created_at"]


admin.site.register(GroundTruth, GroundTruthAdmin)

admin.site.unregister(Group)
