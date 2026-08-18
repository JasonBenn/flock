import os

from django.core.management.base import BaseCommand
import json
from datetime import datetime, timedelta

import pytz
import requests

from flock.management.commands.maybe_post_chill_times import post_slack
from flock.utils import now

WEATHER_URL = (
    f"https://api.darksky.net/forecast/{os.getenv('DARKSKY_API_KEY')}/"
    f"{os.getenv('WEATHER_LATLONG', '37.7749,-122.4194')}"
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        response = requests.get(WEATHER_URL)
        raw_data = json.loads(response.text)
        pdt = pytz.timezone("US/Pacific")
        to_pacific = lambda x: datetime.fromtimestamp(x).astimezone(pdt)
        today = now().astimezone(pdt)

        rain_unlikely = lambda x: x["precipProbability"] <= 0.2
        not_windy = lambda x: x["windSpeed"] <= 10 and x["windGust"] <= 15
        warm = lambda x: x["apparentTemperatureMax"] >= 60
        sunny = lambda x: x["cloudCover"] <= 0.5
        good_visibility = lambda x: x["visibility"] >= 8
        good_sunset = lambda x: sunny(x) and good_visibility(x)

        nice_for_backyard = lambda x: rain_unlikely(x) and warm(x) and sunny(x)
        nice_for_roof = lambda x: good_sunset(x) and not_windy(x)

        weather_day = raw_data["daily"]["data"][1]
        assert to_pacific(weather_day["time"]).date() == today.date() + timedelta(days=1)

        high_temp = weather_day["apparentTemperatureHigh"]
        sunset_time = to_pacific(weather_day["sunsetTime"]).time().strftime("%-I:%mpm")
        summary = weather_day["summary"]
        wind_speed = weather_day["windSpeed"]
        precip_chance = weather_day["precipProbability"]

        if not nice_for_backyard(weather_day):
            return

        message = f"Tomorrow will be {high_temp:.0f}, {summary.lower().strip('.')}, {precip_chance*100:.0f}% chance of rain. Backyard hang?"
        emoji = "palm_tree"

        if nice_for_roof(weather_day):
            message += f"\n\nWind speeds of {wind_speed:.0f}mph, too - roof hang? Sunset's at {sunset_time}."
            emoji = "city_sunset"

        message += "\n\nIf you’re in, mark :sunny:"
        post_slack(message, "chill-times", "Flock", emoji)

        # Nice TODO: the hours when weather is nice
        # weather_hourly = [{**x, **{"time": to_pacific(x["time"])}} for x in (raw_data["hourly"]["data"])]
        # Nice TODO: use the actual Slack API to post a :sunny: reaction
        # requests.get(os.getenv("SLACK_URL"), data=json.dumps({}), headers={"Content-Type": "application/json"})
