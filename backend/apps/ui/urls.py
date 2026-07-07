from django.urls import path

from . import health, views

app_name = "ui"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("sante", health.sante, name="sante"),
]
