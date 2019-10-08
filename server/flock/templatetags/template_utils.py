from datetime import datetime
from datetime import timedelta
from typing import Optional

from django import template
from stringcase import camelcase
from stringcase import snakecase

from django.utils.timezone import localtime

register = template.Library()


def created_at_color(created_at: datetime, current_time: Optional[datetime] = None):
    if current_time is None:
        current_time = localtime()
    if created_at > (current_time - timedelta(minutes=9)):
        color = "black"
    elif created_at > (current_time - timedelta(minutes=12)):
        color = "darkgray"
    else:
        color = "lightgray"
    return color


def snake_case(string):
    return snakecase(string)


def camel_case(string):
    return camelcase(string)


register.filter("created_at_color", created_at_color)
register.filter("snake_case", snake_case)
register.filter("camel_case", camel_case)
