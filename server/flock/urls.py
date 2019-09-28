from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("scans", views.scans, name="scans"),
    path("macs", views.macs, name="macs"),
    path("", include("django.contrib.auth.urls")),
    path("", include("social_django.urls")),
    path("login", views.login, name="login"),
]
