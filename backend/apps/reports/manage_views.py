"""Back-office signalements : la file de traitement des agents.

Seule interface sur mesure du persona agent (docs/spec.md) ; la
configuration passe par l'admin Django.
"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import DetailView, ListView, View

from . import services
from .models import Report, ReportPhoto


class AgentMixin(LoginRequiredMixin, PermissionRequiredMixin):
    permission_required = "reports.view_report"


class QueueView(AgentMixin, ListView):
    template_name = "reports/manage_list.html"
    context_object_name = "reports"
    paginate_by = 25

    def get_queryset(self):
        qs = Report.objects.select_related("category", "category__department")
        statut = self.request.GET.get("statut", "ouverts")
        if statut == "ouverts":
            qs = qs.filter(status__in=Report.OPEN_STATUSES)
        elif statut in Report.Status.values:
            qs = qs.filter(status=statut)
        service = self.request.GET.get("service", "mes")
        my_departments = self.request.user.departments.all()
        if service == "mes" and my_departments.exists():
            qs = qs.filter(category__department__in=my_departments)
        return qs.order_by("created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statut_actif"] = self.request.GET.get("statut", "ouverts")
        context["service_actif"] = self.request.GET.get("service", "mes")
        context["statuts"] = Report.Status.choices
        context["pending_moderation"] = Report.objects.filter(
            publication_state=Report.Publication.PENDING
        ).count()
        return context


class ManageDetailView(AgentMixin, DetailView):
    template_name = "reports/manage_detail.html"
    context_object_name = "report"

    def get_object(self, queryset=None):
        return get_object_or_404(Report, reference=self.kwargs["reference"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuts"] = Report.Status.choices
        context["photos"] = self.object.photos.all()
        context["updates"] = self.object.updates.all()
        return context


class TransitionView(AgentMixin, View):
    permission_required = "reports.change_report"

    def post(self, request, reference):
        report = get_object_or_404(Report, reference=reference)
        try:
            services.transition_report(
                report=report,
                new_status=request.POST.get("new_status", ""),
                public_comment=request.POST.get("public_comment", ""),
                rejection_reason=request.POST.get("rejection_reason", ""),
                author=request.user,
            )
        except ValidationError as exc:
            for errors in exc.message_dict.values():
                for error in errors:
                    messages.error(request, error)
        else:
            messages.success(request, f"Signalement passé à « {report.get_status_display()} ».")
            if report.reporter_email:
                messages.info(request, "Le déclarant a été prévenu par courriel.")
        return redirect("reports:manage_detail", reference=reference)


class ModerationView(AgentMixin, View):
    """Publication du signalement et approbation des photos."""

    permission_required = "reports.change_report"

    def post(self, request, reference):
        report = get_object_or_404(Report, reference=reference)
        action = request.POST.get("action")
        if action in ("publier", "masquer"):
            report.publication_state = (
                Report.Publication.PUBLISHED if action == "publier" else Report.Publication.HIDDEN
            )
            report.save(update_fields=["publication_state"])
            messages.success(
                request,
                "Signalement publié." if action == "publier" else "Signalement masqué.",
            )
        elif action in ("photo_approuver", "photo_rejeter"):
            photo = get_object_or_404(ReportPhoto, pk=request.POST.get("photo"), report=report)
            photo.moderation_state = (
                ReportPhoto.Moderation.APPROVED
                if action == "photo_approuver"
                else ReportPhoto.Moderation.REJECTED
            )
            photo.save(update_fields=["moderation_state"])
            messages.success(request, "Photo modérée.")
        return redirect("reports:manage_detail", reference=reference)
