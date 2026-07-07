"""PWA : service worker, manifest et icônes générées.

Les icônes sont dessinées à la volée (initiale de la commune sur la
couleur d'accent) puis mises en cache disque : aucune image à fournir
pour déployer.
"""

import io

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET
from PIL import Image, ImageDraw

ICON_SIZES = (192, 512)


@require_GET
def service_worker(request):
    content = render_to_string("ui/sw.js", {"version": "1"})
    response = HttpResponse(content, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


@require_GET
def manifest(request):
    commune = settings.CIVIC["COMMUNE_NAME"]
    return JsonResponse(
        {
            "name": commune,
            "short_name": commune[:12],
            "description": f"Application citoyenne de {commune}",
            "lang": "fr",
            "start_url": "/",
            "scope": "/",
            "display": "standalone",
            "background_color": "#F7F6F2",
            "theme_color": settings.CIVIC["ACCENT_COLOR"],
            "icons": [
                {
                    "src": f"/icone-{size}.png",
                    "sizes": f"{size}x{size}",
                    "type": "image/png",
                    "purpose": "any maskable",
                }
                for size in ICON_SIZES
            ],
        },
        content_type="application/manifest+json",
    )


@require_GET
def icon(request, size: int):
    if size not in ICON_SIZES:
        from django.http import Http404

        raise Http404
    cache_path = settings.DATA_DIR / "icons" / f"{size}.png"
    if not cache_path.exists():
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_bytes(_draw_icon(size))
    return HttpResponse(cache_path.read_bytes(), content_type="image/png")


def _draw_icon(size: int) -> bytes:
    accent = settings.CIVIC["ACCENT_COLOR"]
    initial = (settings.CIVIC["COMMUNE_NAME"][:1] or "C").upper()
    image = Image.new("RGB", (size, size), accent)
    draw = ImageDraw.Draw(image)
    from PIL import ImageFont

    try:
        font = ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", int(size * 0.55)
        )
    except OSError:
        font = ImageFont.load_default(size=int(size * 0.5))
    box = draw.textbbox((0, 0), initial, font=font)
    draw.text(
        ((size - box[2] + box[0]) / 2 - box[0], (size - box[3] + box[1]) / 2 - box[1]),
        initial,
        fill="#FFFFFF",
        font=font,
    )
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
