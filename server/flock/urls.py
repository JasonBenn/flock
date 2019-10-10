from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("get_contents", views.get_contents),
    path("scans", views.scans),
    path("macs", views.macs),
    path("debug/<int:person_id>", views.debug),
    path("", include("django.contrib.auth.urls")),
    path("", include("social_django.urls")),
    path("login", views.login),
]
