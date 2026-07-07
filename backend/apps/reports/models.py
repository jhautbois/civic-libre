import secrets

from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.urls import reverse
from django.utils import timezone


class Department(models.Model):
    """Service municipal destinataire (voirie, espaces verts...)."""

    name = models.CharField("nom", max_length=100)
    notification_email = models.EmailField("courriel de notification", blank=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name="agents", blank=True, related_name="departments"
    )

    class Meta:
        verbose_name = "service municipal"
        verbose_name_plural = "services municipaux"

    def __str__(self):
        return self.name


class Category(models.Model):
    """Catégorie de signalement, exposée comme service Open311."""

    code = models.SlugField("code", unique=True, help_text="Stable, sert de service_code Open311.")
    name = models.CharField("nom", max_length=100)
    description = models.CharField("description", max_length=300, blank=True)
    department = models.ForeignKey(
        Department, verbose_name="service destinataire", on_delete=models.PROTECT
    )
    is_active = models.BooleanField("active", default=True)

    class Meta:
        verbose_name = "catégorie"
        ordering = ["name"]

    def __str__(self):
        return self.name


class ReportQuerySet(models.QuerySet):
    def published(self):
        return self.filter(publication_state=Report.Publication.PUBLISHED)


class Report(models.Model):
    """Signalement citoyen (service request Open311)."""

    class Status(models.TextChoices):
        NEW = "new", "À traiter"
        IN_PROGRESS = "in_progress", "En cours"
        RESOLVED = "resolved", "Résolu"
        REJECTED = "rejected", "Rejeté"

    class Publication(models.TextChoices):
        PENDING = "pending", "En attente de modération"
        PUBLISHED = "published", "Publié"
        HIDDEN = "hidden", "Masqué"

    OPEN_STATUSES = (Status.NEW, Status.IN_PROGRESS)

    reference = models.CharField("référence", max_length=20, unique=True)
    category = models.ForeignKey(Category, verbose_name="catégorie", on_delete=models.PROTECT)
    description = models.TextField("description", max_length=4000)
    latitude = models.FloatField("latitude", null=True, blank=True)
    longitude = models.FloatField("longitude", null=True, blank=True)
    address = models.CharField("adresse", max_length=300, blank=True)
    location_hint = models.CharField("précision sur l'emplacement", max_length=200, blank=True)
    status = models.CharField("statut", max_length=20, choices=Status.choices, default=Status.NEW)
    rejection_reason = models.CharField("motif de rejet", max_length=300, blank=True)
    reporter_email = models.EmailField(
        "courriel du déclarant", blank=True, help_text="Jamais publié, purgé à l'anonymisation."
    )
    # Obligation LCEN (art. 6, décret 2021-1362) : conservés 12 mois puis purgés.
    created_ip = models.GenericIPAddressField("IP de création", null=True, blank=True)
    created_user_agent = models.CharField("user-agent", max_length=300, blank=True)
    tracking_token = models.CharField("jeton de suivi", max_length=64)
    publication_state = models.CharField(
        "publication", max_length=20, choices=Publication.choices, default=Publication.PENDING
    )
    created_at = models.DateTimeField("créé le", default=timezone.now)
    closed_at = models.DateTimeField("clos le", null=True, blank=True)
    anonymized_at = models.DateTimeField("anonymisé le", null=True, blank=True)

    objects = ReportQuerySet.as_manager()

    class Meta:
        verbose_name = "signalement"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reference} – {self.category}"

    def get_absolute_url(self):
        return reverse("reports:tracking", args=[self.reference])

    @property
    def is_open(self):
        return self.status in self.OPEN_STATUSES

    @classmethod
    def create_with_reference(cls, **kwargs):
        """Référence lisible R-AAAA-NNNN, séquence par année.

        La contrainte d'unicité tranche les rares collisions (SQLite en
        transactions immédiates les rend déjà improbables).
        """
        year = timezone.now().year
        kwargs.setdefault("tracking_token", secrets.token_urlsafe(32))
        for attempt in range(5):
            try:
                with transaction.atomic():
                    # Le décompte se fait DANS la transaction immédiate :
                    # SQLite sérialise les écrivains dès son ouverture, le
                    # numéro ne peut donc plus être périmé au moment de
                    # l'insertion (l'unicité reste le filet de sécurité).
                    seq = (
                        cls.objects.filter(reference__startswith=f"R-{year}-").count() + 1 + attempt
                    )
                    return cls.objects.create(reference=f"R-{year}-{seq:04d}", **kwargs)
            except IntegrityError:
                continue
        raise IntegrityError("Impossible d'attribuer une référence de signalement")


class ReportUpdate(models.Model):
    """Transition de statut, exposée par l'extension Open311
    servicerequestupdates (format FixMyStreet, docs/spec.md)."""

    report = models.ForeignKey(
        Report, verbose_name="signalement", related_name="updates", on_delete=models.CASCADE
    )
    old_status = models.CharField("ancien statut", max_length=20, choices=Report.Status.choices)
    new_status = models.CharField("nouveau statut", max_length=20, choices=Report.Status.choices)
    public_comment = models.TextField("commentaire public", max_length=1000, blank=True)
    media_url = models.URLField("photo jointe", max_length=500, blank=True)
    author = models.ForeignKey(
        "auth.User", verbose_name="auteur", null=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField("créée le", default=timezone.now)

    class Meta:
        verbose_name = "mise à jour de signalement"
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.report.reference} : {self.get_new_status_display()}"


class ReportPhoto(models.Model):
    class Moderation(models.TextChoices):
        PENDING = "pending", "En attente"
        APPROVED = "approved", "Approuvée"
        REJECTED = "rejected", "Rejetée"

    report = models.ForeignKey(
        Report, verbose_name="signalement", related_name="photos", on_delete=models.CASCADE
    )
    image = models.ImageField("photo", upload_to="signalements/%Y/%m/")
    thumbnail = models.ImageField("miniature", upload_to="signalements/miniatures/%Y/%m/")
    moderation_state = models.CharField(
        "modération", max_length=20, choices=Moderation.choices, default=Moderation.PENDING
    )
    alt_text = models.CharField(
        "texte alternatif", max_length=300, default="Photo jointe au signalement"
    )

    class Meta:
        verbose_name = "photo de signalement"

    def __str__(self):
        return f"Photo de {self.report_id}"
