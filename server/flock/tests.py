from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import localtime

from flock.models import CustomThreshold
from flock.models import Device
from flock.models import DeviceType
from flock.models import GroundTruth
from flock.models import Location
from flock.models import Person
from flock.models import SensorReading
from flock.views import MAX_THRESHOLD
from flock.views import get_estimates
from flock.views import get_current_readings


class LocationEstimationTests(TestCase):
    def setUp(self):
        self.allie = Person.objects.create(first_name="Allie", last_name="Miller")
        self.allie_phone = Device.objects.create(person=self.allie, device_type=DeviceType.PHONE, mac="a")
        self.allie_laptop = Device.objects.create(person=self.allie, device_type=DeviceType.LAPTOP, mac="b")
        self.allie_work_laptop = Device.objects.create(person=self.allie, device_type=DeviceType.WORK_LAPTOP, mac="f")

        self.ben = Person.objects.create(first_name="Ben", last_name="Mann")
        self.ben_phone = Device.objects.create(person=self.ben, device_type=DeviceType.PHONE, mac="c")

        self.michael = Person.objects.create(first_name="Michael", last_name="Lai")
        self.michael_phone = Device.objects.create(person=self.michael, device_type=DeviceType.PHONE, mac="d")

        self.common_room = Location.objects.create(name="Common room")
        self.study = Location.objects.create(name="study")
        self.jasons_room = Location.objects.create(name="Jason's room")

    def test_basic_detection(self):
        """Ben is in the common room"""
        reading = SensorReading.objects.create(device=self.ben_phone, location=self.common_room, rssi=-7)
        locations = get_current_readings()
        self.assertEqual(locations, {self.ben: reading})

    def test_moved_to_another_room(self):
        """Ben went to hang in Jason's room"""
        SensorReading.objects.create(
            device=self.ben_phone, location=self.common_room, rssi=0, created_at=localtime() - timedelta(minutes=5)
        )
        reading = SensorReading.objects.create(device=self.ben_phone, location=self.jasons_room, rssi=0)
        locations = get_current_readings()
        self.assertEqual(locations, {self.ben: reading})

    def test_devices_in_multiple_locations(self):
        """Allie has two devices in different locations - prefer the one with the phone"""
        reading = SensorReading.objects.create(
            device=self.allie_phone, location=self.common_room, rssi=0, created_at=localtime() - timedelta(minutes=1)
        )
        SensorReading.objects.create(device=self.allie_laptop, location=self.jasons_room, rssi=0)
        SensorReading.objects.create(device=self.allie_work_laptop, location=self.jasons_room, rssi=0)
        locations = get_current_readings()
        self.assertEqual(locations, {self.allie: reading})

    def test_ordinary_threshold(self):
        """Ben in backyard, but common room still sees device (weakly)"""
        SensorReading.objects.create(device=self.ben_phone, location=self.common_room, rssi=-25)
        locations = get_current_readings()
        self.assertEqual(locations, {self.ben: None})

    def test_under_threshold_override(self):
        """Ben in his own room, but common room still sees device (weakly)"""
        SensorReading.objects.create(device=self.ben_phone, location=self.common_room, rssi=-7)
        CustomThreshold.objects.create(person=self.ben, location=self.common_room, threshold=-5)
        locations = get_current_readings()
        self.assertEqual(locations, {self.ben: None})

    def test_over_threshold_override(self):
        """Ben in common room with override"""
        reading = SensorReading.objects.create(device=self.ben_phone, location=self.common_room, rssi=-3)
        CustomThreshold.objects.create(person=self.ben, location=self.common_room, threshold=-5)
        locations = get_current_readings()
        self.assertEqual(locations, {self.ben: reading})

    def test_hidden_person_location(self):
        """Allie in Jason's room, ignore"""
        SensorReading.objects.create(device=self.allie_phone, location=self.jasons_room, rssi=0)
        CustomThreshold.objects.create(person=self.allie, location=self.jasons_room, threshold=MAX_THRESHOLD)
        locations = get_current_readings()
        self.assertEqual(locations, {self.allie: None})

    def test_hidden_person_location_with_another_devices_in_another_location(self):
        """Allie really in Jason's room, but laptop in common room"""
        CustomThreshold.objects.create(person=self.allie, location=self.jasons_room, threshold=MAX_THRESHOLD)
        SensorReading.objects.create(device=self.allie_phone, location=self.jasons_room, rssi=0)
        SensorReading.objects.create(device=self.allie_laptop, location=self.common_room, rssi=0)
        locations = get_current_readings()
        self.assertEqual(locations, {self.allie: None})

    def test_hidden_device_in_location(self):
        """Michaels phone always charges in common room, ignore"""
        CustomThreshold.objects.create(device=self.michael_phone, location=self.common_room, threshold=MAX_THRESHOLD)
        SensorReading.objects.create(device=self.michael_phone, location=self.common_room, rssi=0)
        locations = get_current_readings()
        self.assertEqual(locations, {self.michael: None})

    def test_multiple_people_in_location(self):
        """Allie and Michael hanging out in the common room"""
        reading_a = SensorReading.objects.create(device=self.allie_phone, location=self.common_room, rssi=0)
        reading_b = SensorReading.objects.create(device=self.michael_phone, location=self.common_room, rssi=0)
        locations = get_current_readings()
        self.assertEqual(locations, {self.allie: reading_a, self.michael: reading_b})

    def test_present_ground_truth(self):
        """Allie is in the common room"""
        truth = GroundTruth.objects.create(person=self.allie, location=self.common_room, present=True)
        estimates = get_estimates()
        self.assertEqual(estimates, {self.common_room: [truth]})

    def test_not_present_ground_truth(self):
        """Allie is not in the common room"""
        GroundTruth.objects.create(person=self.allie, location=self.common_room, present=False)
        estimates = get_estimates()
        self.assertEqual(estimates, {self.common_room: []})

    def test_ground_truth_in_different_room(self):
        """Allie has a reading from the common room, but someone reports she's really in the Study"""
        SensorReading.objects.create(device=self.allie_phone, location=self.common_room, rssi=0)
        truth = GroundTruth.objects.create(person=self.allie, location=self.study, present=True)
        estimates = get_estimates()
        self.assertEqual(estimates, {self.study: [truth]})

    def test_single_device_moves_between_locations(self):
        """Allie went from Study to Common Room"""
        SensorReading.objects.create(
            device=self.allie_phone, location=self.study, rssi=0, created_at=(localtime() - timedelta(minutes=5))
        )
        common_room_reading = SensorReading.objects.create(device=self.allie_phone, location=self.common_room, rssi=0)
        estimates = get_estimates()
        self.assertEqual(estimates, {self.common_room: [common_room_reading]})

    def test_not_present_report_falls_back_to_another_reading(self):
        """Allie has a reading from the common room, someone reports she's not there, so we fall back to another valid reading from the Study"""
        common_room_reading = SensorReading.objects.create(device=self.allie_phone, location=self.common_room, rssi=0)
        study_reading = SensorReading.objects.create(
            device=self.allie_phone, location=self.study, rssi=0, created_at=localtime() - timedelta(minutes=5)
        )
        estimates = get_estimates()
        self.assertEqual(estimates, {self.common_room: [common_room_reading]})
        GroundTruth.objects.create(person=self.allie, location=self.common_room, present=False)
        estimates = get_estimates()
        self.assertEqual(estimates, {self.study: [study_reading]})
