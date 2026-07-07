from django.urls import path

from . import views

app_name = "announcements"

urlpatterns = [
    path("annonces/<int:pk>/", views.AnnouncementDetailView.as_view(), name="detail"),
    path("gestion/annonces/", views.ManageListView.as_view(), name="manage_list"),
    path("gestion/annonces/nouvelle/", views.ManageCreateView.as_view(), name="manage_create"),
    path("gestion/annonces/<int:pk>/", views.ManageUpdateView.as_view(), name="manage_update"),
    path(
        "gestion/annonces/<int:pk>/supprimer/",
        views.ManageDeleteView.as_view(),
        name="manage_delete",
    ),
]
