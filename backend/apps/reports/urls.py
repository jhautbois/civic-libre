from django.urls import path

from . import manage_views, views

app_name = "reports"

urlpatterns = [
    path("signaler/", views.ReportCreateView.as_view(), name="create"),
    path("suivi/<str:reference>/", views.TrackingView.as_view(), name="tracking"),
    path("signalements/photo/<int:photo_id>/", views.photo, name="photo"),
    path("api/adresse-inverse", views.reverse_geocode_api, name="reverse_geocode"),
    path("gestion/signalements/", manage_views.QueueView.as_view(), name="manage_list"),
    path(
        "gestion/signalements/<str:reference>/",
        manage_views.ManageDetailView.as_view(),
        name="manage_detail",
    ),
    path(
        "gestion/signalements/<str:reference>/statut/",
        manage_views.TransitionView.as_view(),
        name="manage_transition",
    ),
    path(
        "gestion/signalements/<str:reference>/moderation/",
        manage_views.ModerationView.as_view(),
        name="manage_moderate",
    ),
]
