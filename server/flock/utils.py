from datetime import datetime
from enum import Enum

from dateutil import tz
from django.db.models import IntegerField


def now(timezone: str = None):
    if timezone:
        return datetime.now(tz=tz.gettz(timezone))
    return datetime.now(tz.tzutc())
