from django.utils import timezone
from django.views.generic import DetailView, ListView

from .models import MirroredEvent

PAGE_SIZE = 20


class EventListView(ListView):
    template_name = "events/list.html"
    context_object_name = "events"
    paginate_by = PAGE_SIZE

    def get_queryset(self):
        return MirroredEvent.objects.filter(starts_at__gte=timezone.now()).order_by("starts_at")


class EventDetailView(DetailView):
    template_name = "events/detail.html"
    context_object_name = "event"
    model = MirroredEvent
    slug_field = "gancio_id"
    slug_url_kwarg = "gancio_id"

    def get_object(self, queryset=None):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(MirroredEvent, gancio_id=self.kwargs["gancio_id"])
