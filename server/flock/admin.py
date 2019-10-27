from datetime import timedelta

import pytz
from dateutil.parser import parse
from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from flock.models import CustomThreshold, DeviceType
from flock.models import Device
from flock.models import GroundTruth
from flock.models import Location
from flock.models import Person
from flock.models import SensorReading
from flock.utils import now


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
    list_filter = ("location", "person")


admin.site.register(Device, DeviceAdmin)
admin.site.register(CustomThreshold, CustomThresholdAdmin)


def make_readings_current(modeladmin, request, queryset):
    for reading in queryset:
        reading.rssi = 10
        reading.created_at = now()
        reading.save()


make_readings_current.short_description = "Make readings current"


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
            return queryset.filter(created_at__gte=now() - timedelta(minutes=10))
        if self.value() == "last_30":
            return queryset.filter(created_at__gte=now() - timedelta(minutes=30))
        if self.value() == "last_hour":
            return queryset.filter(created_at__gte=now() - timedelta(minutes=60))
        if self.value() == "last_day":
            return queryset.filter(created_at__gte=now() - timedelta(hours=24))
        if self.value() == "last_week":
            return queryset.filter(created_at__gte=now() - timedelta(days=7))


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


class RssiListFilter(admin.SimpleListFilter):
    title = _("rssi")
    parameter_name = "rssi"

    def lookups(self, request, model_admin):
        return [("gte_zero", ">= 0"), ("gte_five", ">= -5"), ("gte_ten", ">= -10")]

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == "gte_zero":
            return queryset.filter(rssi__gte=0)
        if self.value() == "gte_five":
            return queryset.filter(rssi__gte=-5)
        if self.value() == "gte_ten":
            return queryset.filter(rssi__gte=-10)


class FilterableByCreatedAt:
    search_fields = ("created_at",)

    def get_search_results(self, request, queryset, search_term):
        new_queryset, use_distinct = super().get_search_results(request, queryset, search_term)
        try:
            dt = parse(search_term).replace(tzinfo=pytz.UTC)
        except ValueError:
            pass
        else:
            new_queryset = queryset.filter(
                created_at__gte=dt - timedelta(minutes=20), created_at__lte=dt + timedelta(minutes=20)
            )
        return new_queryset, use_distinct


class SensorReadingAdmin(FilterableByCreatedAt, admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ["device", "location", "rssi", "created_at", "present"]
    exclude = ("person", "present")
    list_filter = ("present", "location", CreatedAtListFilter, RssiListFilter, DeviceTypeListFilter, "person")
    actions = [make_readings_current]  # <-- Add the list action function here


admin.site.register(SensorReading, SensorReadingAdmin)


def updated_fixed_at(modeladmin, request, queryset):
    for reading in queryset:
        reading.fixed_at = now()
        reading.save()


updated_fixed_at.short_description = "Update fixed at"


class GroundTruthAdmin(FilterableByCreatedAt, admin.ModelAdmin):
    ordering = ("-created_at",)
    list_display = ["person", "location", "present", "created_at", "fixed_at"]
    list_filter = ("present", "fixed_at", "location", CreatedAtListFilter, "person")
    actions = [updated_fixed_at]


admin.site.register(GroundTruth, GroundTruthAdmin)

admin.site.unregister(Group)
