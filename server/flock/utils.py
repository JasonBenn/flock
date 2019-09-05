from datetime import datetime

from dateutil import tz


def now(timezone: str = None):
    if timezone:
        return datetime.now(tz=tz.gettz(timezone))
    return datetime.now(tz.tzutc())
