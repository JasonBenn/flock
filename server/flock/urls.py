from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("scans", views.scans),
    path("macs", views.macs),
    path("debug_person/<int:person_id>", views.debug_person),
    path("", include("django.contrib.auth.urls")),
    path("", include("social_django.urls")),
    path("login", views.login),
]
