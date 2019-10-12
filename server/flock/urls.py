from django.urls import include, path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("get_contents", views.get_contents),
    path("report_ground_truth", views.report_ground_truth),
    path("ground_truths", views.post_ground_truths),
    path("scans", views.scans),
    path("macs", views.macs),
    path("thanks", views.thanks),
    path("", include("django.contrib.auth.urls")),
    path("", include("social_django.urls")),
    path("login", views.login),
]
