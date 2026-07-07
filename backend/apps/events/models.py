from django.db import models


class MirroredEvent(models.Model):
    """Copie de lecture d'un événement Gancio (voir docs/adr/0002).

    Gancio reste la source de vérité : aucune écriture côté cœur, le
    worker rafraîchit ce miroir sur une fenêtre glissante. Le miroir
    alimente le fil, les pages agenda, les flux iCal et RSS, et le
    déclenchement des notifications (champ ``notified``).
    """

    gancio_id = models.PositiveIntegerField("identifiant Gancio", unique=True)
    title = models.CharField("titre", max_length=200)
    description = models.TextField("description", blank=True)
    starts_at = models.DateTimeField("début")
    ends_at = models.DateTimeField("fin", null=True, blank=True)
    place_name = models.CharField("lieu", max_length=200, blank=True)
    place_address = models.CharField("adresse", max_length=300, blank=True)
    tags = models.JSONField("étiquettes", default=list, blank=True)
    image_url = models.URLField("image", max_length=500, blank=True)
    image_alt = models.CharField("texte alternatif de l'image", max_length=300, blank=True)
    source_url = models.URLField("page Gancio", max_length=500, blank=True)
    notified = models.BooleanField("notification envoyée", default=False)
    first_seen_at = models.DateTimeField("première synchronisation", auto_now_add=True)
    synced_at = models.DateTimeField("dernière synchronisation", auto_now=True)

    class Meta:
        verbose_name = "événement"
        ordering = ["starts_at"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("events:detail", args=[self.gancio_id])
