"""Ré-encodage des photos envoyées : supprime EXIF (dont GPS) et
neutralise les charges utiles en réécrivant les pixels (docs/spec.md,
sécurité). Utilisé pour les signalements et réutilisable ailleurs.
"""

import io

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 8 * 1024 * 1024
MAX_DIMENSION = 2048
THUMB_DIMENSION = 480
JPEG_QUALITY = 85


def reencode_image(uploaded_file, max_dimension=MAX_DIMENSION) -> ContentFile:
    """Renvoie un JPEG propre (sans métadonnées), redimensionné si besoin."""
    if uploaded_file.size > MAX_UPLOAD_BYTES:
        raise ValidationError(
            "La photo dépasse 8 Mo. Choisissez une photo plus légère ou passez cette étape."
        )
    try:
        image = Image.open(uploaded_file)
        # L'orientation EXIF est appliquée AVANT la suppression des métadonnées,
        # sinon les photos de téléphone arrivent couchées.
        image = ImageOps.exif_transpose(image)
        image = image.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise ValidationError(
            "Ce fichier n'est pas une image lisible "
            "(formats acceptés : JPEG, PNG, WebP, HEIC selon le téléphone)."
        ) from exc

    image.thumbnail((max_dimension, max_dimension))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    return ContentFile(buffer.getvalue())


def make_thumbnail(uploaded_file) -> ContentFile:
    uploaded_file.seek(0)
    return reencode_image(uploaded_file, max_dimension=THUMB_DIMENSION)
