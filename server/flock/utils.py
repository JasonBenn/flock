from collections import defaultdict
from datetime import datetime
from typing import Optional

import pytz
from django.conf import settings
from django.db.models import Max


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
    return datetime.now(pytz.UTC)
