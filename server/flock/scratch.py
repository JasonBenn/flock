import json
from datetime import datetime

import pytz
import requests

from flock.utils import now

WEATHER_URL = "https://api.darksky.net/forecast/1f7ee4a765cface784d81701c93c255d/37.765064,-122.426068"
response = requests.get(WEATHER_URL)
raw_data = json.loads(response.text)
pdt = pytz.timezone('US/Pacific')
to_pacific = lambda x: datetime.fromtimestamp(x).astimezone(pdt)
utc_hourly_data = raw_data['hourly']['data']
hourly_data = [{**x, **{'time': to_pacific(x['time'])}} for x in utc_hourly_data]
utc_hourly_data = raw_data['hourly']['data']

today = now().astimezone(pdt)
next_sunset = ...
sunset_times = {to_pacific(x['sunriseTime']) for x in raw_data['daily']['data'][:2]}
sunrise_times = {to_pacific(x['sunriseTime']) for x in raw_data['daily']['data'][:2]}

rain_unlikely = lambda x: x['precipProbability'] <= 0.2
not_windy = lambda x: x['windSpeed'] <= 10 and x['windGust'] <= 15
warm = lambda x: x['apparentTemperature'] >= 60
sunny = lambda x: x['cloudCover'] <= 0.5
good_visibility = lambda x: x['visibility'] >= 8
good_sunset = lambda x: sunny(x) and good_visibility(x)

nice_for_backyard = lambda x: rain_unlikely(x) and warm(x) and sunny(x)
nice_for_roof = lambda x: good_sunset(x) and not_windy(x)

format_time = lambda x: x.strftime("%-I%p")

print("\nbackyard")
for x in [x for x in hourly_data if nice_for_backyard(x)]:
    print(f"{format_time(x['time'])}: {x['apparentTemperature']:.0f}° 🌬 {x['windSpeed']:.1f}mph ☁️ {x['cloudCover'] * 100:.0f}%x")

print("\nroof")
for x in [x for x in hourly_data if nice_for_roof(x)]:
    print(f"{format_time(x['time'])}: {x['apparentTemperature']:.0f}° 🌬 {x['windSpeed']:.1f}mph ☁️ {x['cloudCover'] * 100:.0f}%x")
