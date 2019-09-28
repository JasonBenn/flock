from datetime import datetime
from datetime import timedelta

from django import template
from stringcase import camelcase
from stringcase import snakecase

from flock.utils import now

register = template.Library()


def created_at_color(created_at: datetime):
    time = now()
    if created_at > (time - timedelta(minutes=9)):
        color = "black"
    elif created_at > (time - timedelta(minutes=12)):
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
