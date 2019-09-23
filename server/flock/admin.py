from django.contrib import admin

# Register your models here.
from flock.models import Location, Person, Device, Position

admin.site.register(Location)
admin.site.register(Person)
admin.site.register(Device)
admin.site.register(Position)
