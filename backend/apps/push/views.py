from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView

from .models import TOPICS


@method_decorator(ensure_csrf_cookie, name="dispatch")
class SettingsView(TemplateView):
    """Page réglages : opt-in explicite, sujets, tutoriel iOS accessible."""

    template_name = "push/settings.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["topics"] = TOPICS
        return context
