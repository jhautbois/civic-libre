"""Couche service : une seule voie de création de signalement, partagée
par le formulaire citoyen et le POST Open311 (docs/spec.md)."""

import os

from django.core.exceptions import ValidationError

from . import geocoding
from .images import make_thumbnail, reencode_image
from .models import Category, Report, ReportPhoto


def create_report(
    *,
    category: Category,
    description: str,
    latitude: float | None = None,
    longitude: float | None = None,
    address: str = "",
    location_hint: str = "",
    reporter_email: str = "",
    photo_file=None,
    ip: str | None = None,
    user_agent: str = "",
) -> Report:
    description = (description or "").strip()
    if not description:
        raise ValidationError({"description": "Décrivez le problème en quelques mots."})
    if latitude is None and longitude is None and not address.strip():
        raise ValidationError(
            {"address": "Indiquez où se trouve le problème : sur la carte ou par une adresse."}
        )

    # Géocodage complémentaire, jamais bloquant (Open311 accepte l'un ou l'autre).
    if latitude is not None and longitude is not None and not address:
        address = geocoding.reverse(latitude, longitude)
    elif address and latitude is None:
        found = geocoding.search(address)
        if found:
            latitude, longitude, address = found

    report = Report.create_with_reference(
        category=category,
        description=description[:4000],
        latitude=latitude,
        longitude=longitude,
        address=address[:300],
        location_hint=location_hint[:200],
        reporter_email=reporter_email,
        created_ip=ip,
        created_user_agent=user_agent[:300],
    )

    if photo_file is not None:
        main = reencode_image(photo_file)
        thumb = make_thumbnail(photo_file)
        base = os.path.splitext(os.path.basename(photo_file.name or "photo"))[0][:40] or "photo"
        photo = ReportPhoto(report=report)
        photo.image.save(f"{report.reference}-{base}.jpg", main, save=False)
        photo.thumbnail.save(f"{report.reference}-{base}-min.jpg", thumb, save=False)
        photo.save()

    return report
