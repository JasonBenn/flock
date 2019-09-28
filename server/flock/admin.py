from django.contrib import admin
from django.contrib.auth.models import Group

from flock.models import Device, Location, Person, SensorReading


class LocationAdmin(admin.ModelAdmin):
    ordering = ("name",)


admin.site.register(Location, LocationAdmin)


class PersonAdmin(admin.ModelAdmin):
    ordering = ("first_name",)


admin.site.register(Person, PersonAdmin)


class DeviceAdmin(admin.ModelAdmin):
    ordering = ("person__first_name",)


admin.site.register(Device, DeviceAdmin)
admin.site.register(SensorReading)

admin.site.unregister(Group)
