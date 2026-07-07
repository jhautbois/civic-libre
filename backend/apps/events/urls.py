from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.EventListView.as_view(), name="list"),
    path("<int:gancio_id>/", views.EventDetailView.as_view(), name="detail"),
]
