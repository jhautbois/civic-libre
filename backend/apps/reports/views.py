from django.contrib import messages
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import FormView, TemplateView

from . import geocoding, services, throttle
from .forms import ReportForm
from .models import Report, ReportPhoto


class ReportCreateView(FormView):
    template_name = "reports/form.html"
    form_class = ReportForm

    def post(self, request, *args, **kwargs):
        if not throttle.allow(request, "signalement"):
            messages.error(
                request,
                "Trop de signalements envoyés depuis votre connexion. "
                "Réessayez dans une heure, ou appelez la mairie.",
            )
            return self.get(request, *args, **kwargs)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        data = form.cleaned_data
        report = services.create_report(
            category=data["category"],
            description=data["description"],
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            address=data.get("address", ""),
            location_hint=data.get("location_hint", ""),
            reporter_email=data.get("reporter_email", ""),
            photo_file=data.get("photo"),
            ip=throttle.client_ip(self.request),
            user_agent=self.request.META.get("HTTP_USER_AGENT", ""),
        )
        return redirect(f"{report.get_absolute_url()}?jeton={report.tracking_token}&nouveau=1")


class TrackingView(TemplateView):
    """Suivi public : contenus publiés seulement ; le jeton révèle au
    déclarant son propre signalement en attente de modération."""

    template_name = "reports/tracking.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = get_object_or_404(Report, reference=kwargs["reference"])
        token = self.request.GET.get("jeton", "")
        is_owner = bool(token) and token == report.tracking_token
        is_published = report.publication_state == Report.Publication.PUBLISHED
        context.update(
            {
                "report": report,
                "is_owner": is_owner,
                "show_content": is_published or is_owner,
                "is_new": self.request.GET.get("nouveau") == "1" and is_owner,
                "photos": report.photos.filter(moderation_state=ReportPhoto.Moderation.APPROVED)
                if not is_owner
                else report.photos.all(),
                "updates": report.updates.all() if hasattr(report, "updates") else [],
            }
        )
        return context


def photo(request, photo_id):
    """Les photos ne sont jamais servies depuis /media : approbation ou jeton requis."""
    photo = get_object_or_404(ReportPhoto, pk=photo_id)
    approved = photo.moderation_state == ReportPhoto.Moderation.APPROVED
    published = photo.report.publication_state == Report.Publication.PUBLISHED
    is_owner = request.GET.get("jeton", "") == photo.report.tracking_token
    is_agent = request.user.is_authenticated and request.user.has_perm("reports.view_report")
    if not ((approved and published) or is_owner or is_agent):
        raise Http404
    variant = photo.thumbnail if request.GET.get("taille") == "min" else photo.image
    return FileResponse(variant.open("rb"), content_type="image/jpeg")


def reverse_geocode_api(request):
    """Petit relais JSON pour la carte : l'IP de l'habitant ne part pas
    chez le géocodeur, et la CSP reste connect-src 'self'."""
    if not throttle.allow(request, "geocodage", limit=60):
        return JsonResponse({"label": ""}, status=429)
    try:
        latitude = float(request.GET["lat"])
        longitude = float(request.GET["lon"])
    except (KeyError, ValueError):
        return JsonResponse({"label": ""}, status=400)
    return JsonResponse({"label": geocoding.reverse(latitude, longitude)})
