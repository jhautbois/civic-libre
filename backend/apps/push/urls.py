from django.urls import path

from . import api, views

app_name = "push"

urlpatterns = [
    path("notifications/", views.SettingsView.as_view(), name="settings"),
    path("api/push/cle", api.public_key, name="public_key"),
    path("api/push/abonnement", api.subscribe, name="subscribe"),
    path("api/push/desabonnement", api.unsubscribe, name="unsubscribe"),
]
