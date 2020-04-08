from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Optional

from django import template
from stringcase import camelcase
from stringcase import snakecase

from flock.models import GroundTruth
from flock.utils import now

register = template.Library()


@register.filter
def created_at_color(created_at: datetime, current_time: Optional[datetime] = None):
    if current_time is None:
        current_time = now()
    if created_at > (current_time - timedelta(minutes=9)):
        color = "black"
    elif created_at > (current_time - timedelta(minutes=12)):
        color = "darkgray"
    else:
        color = "lightgray"
    return color


@register.filter
def snake_case(string):
    return snakecase(string)


@register.filter
def camel_case(string):
    return camelcase(string)


@register.filter
def is_ground_truth(instance: Any) -> bool:
    return isinstance(instance, GroundTruth)


@register.filter
def brief_time(dt: datetime) -> str:
    delta = now() - dt
    if delta.days > 1:
        return f"{delta.days} days"
    else:
        return f"{delta.seconds // 3600} hours"
