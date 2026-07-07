from django.db import models
from django.utils import timezone

TOPICS = [
    ("events", "Événements"),
    ("news", "Actualités"),
    ("alerts", "Alertes"),
]


class PushSubscription(models.Model):
    """Abonnement Web Push d'un navigateur (RFC 8030/8291/8292).

    Aucune donnée personnelle : l'endpoint est une URL opaque fournie
    par le service de push du navigateur.
    """

    endpoint = models.URLField("endpoint", max_length=500, unique=True)
    p256dh = models.CharField("clé p256dh", max_length=200)
    auth = models.CharField("clé auth", max_length=100)
    topics = models.JSONField("sujets", default=list)
    created_at = models.DateTimeField("créé le", default=timezone.now)
    last_success_at = models.DateTimeField("dernier succès", null=True, blank=True)
    failure_count = models.PositiveIntegerField("échecs consécutifs", default=0)

    class Meta:
        verbose_name = "abonnement aux notifications"

    def __str__(self):
        return f"Abonnement {self.pk}"


class OutgoingNotification(models.Model):
    """Outbox : les alertes passent devant tout (docs/adr/0005)."""

    class Priority(models.TextChoices):
        ALERT = "alert", "Alerte"
        NORMAL = "normal", "Normale"

    class State(models.TextChoices):
        PENDING = "pending", "À envoyer"
        SENDING = "sending", "Envoi en cours"
        DONE = "done", "Envoyée"

    topic = models.CharField("sujet", max_length=20, choices=TOPICS)
    priority = models.CharField(
        "priorité", max_length=10, choices=Priority.choices, default=Priority.NORMAL
    )
    title = models.CharField("titre", max_length=120)
    body = models.CharField("texte", max_length=300, blank=True)
    url = models.CharField("lien", max_length=300, default="/")
    state = models.CharField("état", max_length=10, choices=State.choices, default=State.PENDING)
    created_at = models.DateTimeField("créée le", default=timezone.now)
    sent_at = models.DateTimeField("envoyée le", null=True, blank=True)

    class Meta:
        verbose_name = "notification sortante"
        ordering = ["created_at"]

    def __str__(self):
        return self.title


class NotificationDelivery(models.Model):
    """Livraison par abonnement : idempotence at-least-once sans doublon."""

    class State(models.TextChoices):
        PENDING = "pending", "À livrer"
        SENT = "sent", "Livrée"
        FAILED = "failed", "En échec"
        GONE = "gone", "Abonnement disparu"

    notification = models.ForeignKey(
        OutgoingNotification, related_name="deliveries", on_delete=models.CASCADE
    )
    subscription = models.ForeignKey(
        PushSubscription, related_name="deliveries", on_delete=models.CASCADE
    )
    state = models.CharField(max_length=10, choices=State.choices, default=State.PENDING)
    attempts = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["notification", "subscription"], name="delivery_unique")
        ]

    def __str__(self):
        return f"Livraison {self.notification_id} vers {self.subscription_id}"
