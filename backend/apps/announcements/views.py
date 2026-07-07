from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import AnnouncementForm
from .models import Announcement


class AnnouncementDetailView(DetailView):
    template_name = "announcements/detail.html"
    context_object_name = "announcement"

    def get_queryset(self):
        return Announcement.objects.visible()


class ManageMixin(LoginRequiredMixin, PermissionRequiredMixin):
    """Accès réservé aux gestionnaires (groupe créé par migration)."""

    raise_exception = False  # redirection vers la connexion


class ManageListView(ManageMixin, ListView):
    permission_required = "announcements.view_announcement"
    template_name = "announcements/manage_list.html"
    context_object_name = "announcements"
    queryset = Announcement.objects.all()
    paginate_by = 20


class ManageCreateView(ManageMixin, SuccessMessageMixin, CreateView):
    permission_required = "announcements.add_announcement"
    template_name = "announcements/manage_form.html"
    form_class = AnnouncementForm
    success_url = reverse_lazy("announcements:manage_list")
    success_message = "Annonce publiée."

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class ManageUpdateView(ManageMixin, SuccessMessageMixin, UpdateView):
    permission_required = "announcements.change_announcement"
    template_name = "announcements/manage_form.html"
    form_class = AnnouncementForm
    queryset = Announcement.objects.all()
    success_url = reverse_lazy("announcements:manage_list")
    success_message = "Annonce mise à jour."


class ManageDeleteView(ManageMixin, SuccessMessageMixin, DeleteView):
    permission_required = "announcements.delete_announcement"
    template_name = "announcements/manage_confirm_delete.html"
    queryset = Announcement.objects.all()
    success_url = reverse_lazy("announcements:manage_list")
    success_message = "Annonce supprimée."
