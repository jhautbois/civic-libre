from django.urls import re_path

from . import open311

app_name = "open311"

urlpatterns = [
    re_path(r"^discovery\.(?P<fmt>json|xml)$", open311.discovery, name="discovery"),
    re_path(r"^services\.(?P<fmt>json|xml)$", open311.services_list, name="services"),
    re_path(
        r"^services/(?P<code>[\w-]+)\.(?P<fmt>json|xml)$",
        open311.service_definition,
        name="service_definition",
    ),
    re_path(
        r"^requests\.(?P<fmt>json|xml)$", open311.requests_collection, name="requests"
    ),
    re_path(
        r"^requests/(?P<request_id>[\w-]+)\.(?P<fmt>json|xml)$",
        open311.request_detail,
        name="request_detail",
    ),
    re_path(
        r"^tokens/(?P<token_id>[\w-]+)\.(?P<fmt>json|xml)$",
        open311.token_detail,
        name="token",
    ),
    re_path(
        r"^servicerequestupdates\.(?P<fmt>json|xml)$",
        open311.request_updates,
        name="updates",
    ),
]
