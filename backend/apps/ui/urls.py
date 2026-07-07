from django.urls import path
from django.views.generic import TemplateView

from . import health, views

app_name = "ui"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("sante", health.sante, name="sante"),
    path(
        "infos/",
        TemplateView.as_view(template_name="ui/infos.html"),
        name="infos",
    ),
    path(
        "confidentialite/",
        TemplateView.as_view(template_name="ui/privacy.html"),
        name="privacy",
    ),
    path(
        "accessibilite/",
        TemplateView.as_view(template_name="ui/accessibility.html"),
        name="accessibility",
    ),
]
