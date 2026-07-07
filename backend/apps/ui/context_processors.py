from django.conf import settings


def civic(request):
    """Expose les réglages de la commune à tous les gabarits."""
    return {"civic": settings.CIVIC}
