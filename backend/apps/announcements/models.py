from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone


class AnnouncementQuerySet(models.QuerySet):
    def visible(self):
        """Publiées et non expirées, les seules montrées aux habitants."""
        now = timezone.now()
        return self.filter(published_at__lte=now).exclude(expires_at__lt=now)

    def alerts(self):
        return self.visible().filter(level=Announcement.Level.ALERT)

    def news(self):
        return self.visible().filter(level=Announcement.Level.INFO)


class Announcement(models.Model):
    """Annonce de la mairie : actualité ou alerte, diffusée en une saisie
    vers le fil, le flux RSS et les notifications (lot 6)."""

    class Level(models.TextChoices):
        INFO = "info", "Information"
        ALERT = "alert", "Alerte"

    title = models.CharField("titre", max_length=200)
    body = models.TextField("texte")
    level = models.CharField("niveau", max_length=10, choices=Level.choices, default=Level.INFO)
    image = models.ImageField("image", upload_to="annonces/", blank=True)
    image_is_decorative = models.BooleanField("image décorative", default=False)
    image_alt = models.CharField(
        "texte alternatif",
        max_length=300,
        blank=True,
        help_text="Obligatoire si l'image apporte une information (RGAA 1.1).",
    )
    is_pinned = models.BooleanField("épinglée", default=False)
    published_at = models.DateTimeField("publiée le", default=timezone.now)
    expires_at = models.DateTimeField("expire le", null=True, blank=True)
    notified = models.BooleanField("notification envoyée", default=False)
    created_by = models.ForeignKey(
        "auth.User",
        verbose_name="créée par",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    objects = AnnouncementQuerySet.as_manager()

    class Meta:
        verbose_name = "annonce"
        ordering = ["-is_pinned", "-published_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("announcements:detail", args=[self.pk])

    def clean(self):
        if self.image and not self.image_is_decorative and not self.image_alt.strip():
            raise ValidationError(
                {
                    "image_alt": "Décrivez l'image en quelques mots, ou cochez "
                    "« image décorative » si elle n'apporte rien au texte."
                }
            )
        if self.expires_at and self.expires_at <= self.published_at:
            raise ValidationError({"expires_at": "L'expiration doit suivre la publication."})
