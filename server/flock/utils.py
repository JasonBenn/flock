from datetime import datetime
from enum import Enum

from dateutil import tz
from django.db.models import IntegerField


def now(timezone: str = None):
    if timezone:
        return datetime.now(tz=tz.gettz(timezone))
    return datetime.now(tz.tzutc())


class IntegerEnumField(IntegerField):
    # Copied from github.com/joshalbrecht/sourceress
    def __init__(self, *args, enum_type=None, **kwargs):
        assert enum_type is not None
        if "choices" in kwargs:
            del kwargs["choices"]
        default = kwargs.get("default")
        if isinstance(default, Enum):
            kwargs["default"] = default.value

        super().__init__(*args, choices=enum_type.choices(), **kwargs)
        self.enum_type = enum_type

    def value_from_object(self, obj):
        value = getattr(obj, self.attname)
        if value is None:
            return None
        return value.value

    def clean(self, value, model_instance):
        value = self.to_python(value)
        python_value = value
        if value:
            value = value.value
        self.validate(value, model_instance)
        self.run_validators(value)
        return python_value

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["enum_type"] = self.enum_type
        return name, path, args, kwargs

    # noinspection PyUnusedLocal
    def from_db_value(self, value, expression, connection, context):
        if value == None:
            return value
        return self.enum_type(value)

    def to_python(self, value):
        if isinstance(value, self.enum_type):
            return value

        if value is None:
            return None

        return self.enum_type(value)

    def get_prep_value(self, value):
        if value is None:
            return None
        if isinstance(value, int):
            enum_value = self.enum_type(value)  # this will and should fail if the value given is not a valid choice
            return enum_value.value
        if isinstance(value, float):
            assert int(value) == round(value)
            enum_value = self.enum_type(
                int(value)
            )  # this will and should fail if the value given is not a valid choice
            return enum_value.value
        return value.value

    def value_to_string(self, obj):
        value = self.value_from_object(obj)
        if value is None:
            return None
        return str(value)


class DjangoChoicesConstant(Enum):
    # Copied from github.com/joshalbrecht/sourceress
    @classmethod
    def choices(cls):
        return ((name, member.value) for name, member in cls.__members__.items())
