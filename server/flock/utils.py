import json
import os
from collections import defaultdict
from datetime import datetime
from typing import Optional

import pytz
import requests
from django.conf import settings
from django.db.models import Max
from django.utils import timezone


def group_by(iterable, key):
    grouped = defaultdict(list)
    for x in iterable:
        grouped[key(x)].append(x)
    return {k: list(v) for k, v in grouped.items()}


def get_at_time(at_time: Optional[datetime] = None) -> datetime:
    if settings.FREEZE_TIME:
        from flock.models import SensorReading

        return SensorReading.objects.aggregate(Max("created_at"))["created_at__max"]
    else:
        if at_time:
            return at_time
        else:
            return now()


def now() -> datetime:
    return timezone.now()


def friendly_time(dt: datetime) -> str:
    return dt.strftime("%-m/%-d %-I:%M %p")


def as_pdt(dt: datetime) -> datetime:
    pdt = pytz.timezone("America/Los_Angeles")
    return dt.astimezone(pdt)


def title_case(string: str) -> str:
    return " ".join([x[0].upper() + x[1:] for x in string.split(" ")])


def post_slack(message, channel, username="Flock", icon_emoji="bird"):
    data = {"channel": f"#{channel}", "username": username, "text": message, "icon_emoji": f":{icon_emoji}:"}
    return requests.post(os.getenv("SLACK_URL"), data=json.dumps(data), headers={"Content-Type": "application/json"})
