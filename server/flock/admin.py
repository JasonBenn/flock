from datetime import date, timedelta

from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.timezone import localtime
from django.utils.translation import gettext_lazy as _

from flock.models import CustomThreshold, DeviceType
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


class CreatedAtListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("created at")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "created_at"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ("last_10", _("last 10 minutes")),
            ("last_30", _("last 30 minutes")),
            ("last_hour", _("last hour")),
            ("last_day", _("last day")),
            ("last_week", _("last week")),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == "last_10":
            return queryset.filter(created_at__gte=localtime() - timedelta(minutes=10))
        if self.value() == "last_30":
            return queryset.filter(created_at__gte=localtime() - timedelta(minutes=30))
        if self.value() == "last_hour":
            return queryset.filter(created_at__gte=localtime() - timedelta(minutes=60))
        if self.value() == "last_day":
            return queryset.filter(created_at__gte=localtime() - timedelta(hours=24))
        if self.value() == "last_week":
            return queryset.filter(created_at__gte=localtime() - timedelta(days=7))


class DeviceTypeListFilter(admin.SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = _("device")

    # Parameter for the filter that will be used in the URL query.
    parameter_name = "device_type"

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return [(key.lower(), key.lower()) for key, value in DeviceType.items()]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value():
            return queryset.filter(device__device_type=DeviceType.get(self.value()).value)


class SensorReadingAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ["device", "location", "rssi", "created_at", "present"]
    exclude = ("person", "present")
    list_filter = ("present", "location", CreatedAtListFilter, DeviceTypeListFilter, "person")
    actions = [rssi_to_ten]  # <-- Add the list action function here


admin.site.register(SensorReading, SensorReadingAdmin)


class GroundTruthAdmin(admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ["person", "location", "present", "created_at"]


admin.site.register(GroundTruth, GroundTruthAdmin)

admin.site.unregister(Group)
