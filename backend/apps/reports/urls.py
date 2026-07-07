from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("signaler/", views.ReportCreateView.as_view(), name="create"),
    path("suivi/<str:reference>/", views.TrackingView.as_view(), name="tracking"),
    path("signalements/photo/<int:photo_id>/", views.photo, name="photo"),
    path("api/adresse-inverse", views.reverse_geocode_api, name="reverse_geocode"),
]
