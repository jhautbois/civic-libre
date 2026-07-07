from django.utils import timezone
from django.views.generic import TemplateView

from apps.announcements.models import Announcement
from apps.events.models import MirroredEvent


class HomeView(TemplateView):
    template_name = "ui/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["alerts"] = Announcement.objects.alerts()
        context["news"] = Announcement.objects.news()[:5]
        context["upcoming_events"] = MirroredEvent.objects.filter(
            starts_at__gte=timezone.now()
        ).order_by("starts_at")[:5]
        return context
