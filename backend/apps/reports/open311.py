"""API Open311 GeoReport v2 (docs/spec.md, tableau normatif).

Choix de conformité :
- XML obligatoire du standard et JSON optionnel, sélectionnés par le
  suffixe d'URL ; le POST est en formulaire (le standard n'envoie pas
  de corps XML), aucune analyse XML d'entrée n'a donc lieu.
- Mode temps réel : le POST renvoie toujours service_request_id (la
  référence publique), jamais de token ; GET /tokens est trivial.
- Statuts : open et closed dans le champ status du standard ; les
  statuts détaillés passent par l'extension FixMyStreet
  servicerequestupdates avec les états étendus (Additional states).
- Minimisation : description, adresse et photos ne sont exposées que
  pour les signalements publiés (modérés) ; le courriel du déclarant
  n'apparaît jamais.
"""

import datetime
import xml.etree.ElementTree as ET

from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseNotAllowed, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from . import services, throttle
from .models import Category, Report, ReportPhoto, ReportUpdate

STATUS_TO_OPEN311 = {
    Report.Status.NEW: "open",
    Report.Status.IN_PROGRESS: "open",
    Report.Status.RESOLVED: "closed",
    Report.Status.REJECTED: "closed",
}

# Extension FixMyStreet « Additional states » pour les updates.
STATUS_TO_EXTENDED = {
    Report.Status.NEW: "OPEN",
    Report.Status.IN_PROGRESS: "IN_PROGRESS",
    Report.Status.RESOLVED: "FIXED",
    Report.Status.REJECTED: "NO_FURTHER_ACTION",
}

WINDOW_DAYS = 90


def _iso(dt):
    return timezone.localtime(dt).isoformat() if dt else ""


def _respond(request, fmt, root_tag, items, item_tag):
    """Sérialise une liste de dictionnaires plats en JSON ou XML."""
    if fmt == "json":
        return JsonResponse(items, safe=False, json_dumps_params={"ensure_ascii": False})
    root = ET.Element(root_tag)
    for item in items:
        node = ET.SubElement(root, item_tag)
        for key, value in item.items():
            child = ET.SubElement(node, key)
            if value is not None and value != "":
                child.text = str(value)
    payload = ET.tostring(root, encoding="unicode", xml_declaration=False)
    return HttpResponse(
        f'<?xml version="1.0" encoding="utf-8"?>{payload}',
        content_type="text/xml; charset=utf-8",
    )


def _error(request, fmt, code, description):
    response = _respond(
        request,
        fmt,
        "errors",
        [{"code": code, "description": description}],
        "error",
    )
    response.status_code = code
    return response


def discovery(request, fmt):
    base = request.build_absolute_uri("/open311/v2")
    items = [
        {
            "changeset": "2026-07-07",
            "contact": "La mairie, voir la page infos du site",
            "key_service": "Aucune clef requise en lecture",
            "endpoints": None,
        }
    ]
    if fmt == "json":
        return JsonResponse(
            {
                "discovery": {
                    "changeset": items[0]["changeset"],
                    "contact": items[0]["contact"],
                    "key_service": items[0]["key_service"],
                    "endpoints": [
                        {
                            "specification": "http://wiki.open311.org/GeoReport_v2",
                            "url": base,
                            "changeset": items[0]["changeset"],
                            "type": "production",
                            "formats": ["text/xml", "application/json"],
                        }
                    ],
                }
            }
        )
    root = ET.Element("discovery")
    ET.SubElement(root, "changeset").text = items[0]["changeset"]
    ET.SubElement(root, "contact").text = items[0]["contact"]
    ET.SubElement(root, "key_service").text = items[0]["key_service"]
    endpoints = ET.SubElement(root, "endpoints")
    endpoint = ET.SubElement(endpoints, "endpoint")
    ET.SubElement(endpoint, "specification").text = "http://wiki.open311.org/GeoReport_v2"
    ET.SubElement(endpoint, "url").text = base
    ET.SubElement(endpoint, "changeset").text = items[0]["changeset"]
    ET.SubElement(endpoint, "type").text = "production"
    formats = ET.SubElement(endpoint, "formats")
    ET.SubElement(formats, "format").text = "text/xml"
    ET.SubElement(formats, "format").text = "application/json"
    payload = ET.tostring(root, encoding="unicode")
    return HttpResponse(
        f'<?xml version="1.0" encoding="utf-8"?>{payload}',
        content_type="text/xml; charset=utf-8",
    )


def _service_dict(category):
    return {
        "service_code": category.code,
        "service_name": category.name,
        "description": category.description,
        "metadata": "false",
        "type": "realtime",
        "keywords": "",
        "group": category.department.name,
    }


def services_list(request, fmt):
    items = [_service_dict(c) for c in Category.objects.filter(is_active=True)]
    return _respond(request, fmt, "services", items, "service")


def service_definition(request, code, fmt):
    try:
        category = Category.objects.get(code=code, is_active=True)
    except Category.DoesNotExist:
        return _error(request, fmt, 404, f"service_code {code} inconnu")
    return _respond(request, fmt, "services", [_service_dict(category)], "service")


def _request_dict(request, report):
    published = report.publication_state == Report.Publication.PUBLISHED
    last_update = report.updates.order_by("-created_at").first()
    media_url = ""
    if published:
        photo = report.photos.filter(moderation_state=ReportPhoto.Moderation.APPROVED).first()
        if photo:
            media_url = request.build_absolute_uri(f"/signalements/photo/{photo.pk}/")
    return {
        "service_request_id": report.reference,
        "status": STATUS_TO_OPEN311[report.status],
        "status_notes": (last_update.public_comment if last_update else "")[:500]
        if published
        else "",
        "service_name": report.category.name,
        "service_code": report.category.code,
        "description": report.description if published else "",
        "agency_responsible": report.category.department.name,
        "service_notice": "",
        "requested_datetime": _iso(report.created_at),
        "updated_datetime": _iso(last_update.created_at if last_update else report.created_at),
        "expected_datetime": "",
        "address": report.address if published else "",
        "address_id": "",
        "zipcode": "",
        # Position exposée seulement après modération : la charte impose
        # de pouvoir généraliser la localisation avant publication.
        "lat": report.latitude if published and report.latitude is not None else "",
        "long": report.longitude if published and report.longitude is not None else "",
        "media_url": media_url,
    }


@csrf_exempt
def requests_collection(request, fmt):
    if request.method == "POST":
        return _create_request(request, fmt)
    if request.method != "GET":
        return HttpResponseNotAllowed(["GET", "POST"])

    # Liste publique : contenus à l'état publié uniquement (docs/spec.md).
    qs = Report.objects.published().select_related("category", "category__department")
    ids = request.GET.get("service_request_id")
    if ids:
        qs = qs.filter(reference__in=[i.strip() for i in ids.split(",")])
    code = request.GET.get("service_code")
    if code:
        qs = qs.filter(category__code=code)
    status = request.GET.get("status")
    if status in ("open", "closed"):
        wanted = [s for s, o in STATUS_TO_OPEN311.items() if o == status]
        qs = qs.filter(status__in=wanted)
    start = _parse_date(request.GET.get("start_date"))
    end = _parse_date(request.GET.get("end_date"))
    if not start and not ids:
        start = timezone.now() - datetime.timedelta(days=WINDOW_DAYS)
    if start:
        qs = qs.filter(created_at__gte=start)
    if end:
        qs = qs.filter(created_at__lte=end)

    items = [_request_dict(request, r) for r in qs.order_by("-created_at")[:1000]]
    return _respond(request, fmt, "service_requests", items, "request")


def _parse_date(raw):
    if not raw:
        return None
    try:
        parsed = datetime.datetime.fromisoformat(raw)
    except ValueError:
        return None
    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, datetime.UTC)
    return parsed


def _create_request(request, fmt):
    if not throttle.allow(request, "open311"):
        return _error(request, fmt, 429, "Trop de requêtes, réessayez plus tard")

    code = request.POST.get("service_code", "")
    try:
        category = Category.objects.get(code=code, is_active=True)
    except Category.DoesNotExist:
        return _error(request, fmt, 404, f"service_code {code} inconnu ou manquant")

    def _float(name):
        value = request.POST.get(name, "")
        try:
            return float(value)
        except ValueError:
            return None

    try:
        report = services.create_report(
            category=category,
            description=request.POST.get("description", ""),
            latitude=_float("lat"),
            longitude=_float("long"),
            address=request.POST.get("address_string", ""),
            reporter_email=request.POST.get("email", ""),
            ip=throttle.client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
    except ValidationError as exc:
        first = next(iter(exc.message_dict.values()))[0]
        return _error(request, fmt, 400, first)

    # media_url entrante : stockée comme référence, jamais téléchargée (SSRF).
    media_url = request.POST.get("media_url", "")[:500]
    if media_url:
        ReportUpdate.objects.create(
            report=report,
            old_status=report.status,
            new_status=report.status,
            public_comment="",
            media_url=media_url,
        )

    items = [
        {
            "service_request_id": report.reference,
            "service_notice": "Signalement enregistré, suivi sur "
            + request.build_absolute_uri(report.get_absolute_url()),
            "account_id": "",
        }
    ]
    response = _respond(request, fmt, "service_requests", items, "request")
    response.status_code = 201
    return response


def request_detail(request, request_id, fmt):
    try:
        report = Report.objects.get(reference=request_id)
    except Report.DoesNotExist:
        return _error(request, fmt, 404, f"service_request_id {request_id} inconnu")
    return _respond(request, fmt, "service_requests", [_request_dict(request, report)], "request")


def token_detail(request, token_id, fmt):
    """Mode temps réel : un token EST déjà l'identifiant définitif."""
    items = [{"service_request_id": token_id, "token": token_id}]
    return _respond(request, fmt, "service_requests", items, "request")


def request_updates(request, fmt):
    """Extension FixMyStreet : GET servicerequestupdates."""
    qs = (
        ReportUpdate.objects.filter(report__publication_state=Report.Publication.PUBLISHED)
        .select_related("report")
        .order_by("created_at")
    )
    start = _parse_date(request.GET.get("start_date"))
    end = _parse_date(request.GET.get("end_date"))
    if start:
        qs = qs.filter(created_at__gte=start)
    if end:
        qs = qs.filter(created_at__lte=end)
    ids = request.GET.get("service_request_id")
    if ids:
        qs = qs.filter(report__reference__in=[i.strip() for i in ids.split(",")])

    items = [
        {
            "update_id": str(update.pk),
            "service_request_id": update.report.reference,
            "status": STATUS_TO_EXTENDED[update.new_status],
            "updated_datetime": _iso(update.created_at),
            "description": update.public_comment,
            # media_url stockée au POST = URL fournie par le déclarant :
            # jamais republiée sans modération (docs/spec.md).
            "media_url": "",
        }
        for update in qs[:1000]
    ]
    return _respond(request, fmt, "service_request_updates", items, "request_update")
