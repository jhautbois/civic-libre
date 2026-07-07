"""Dérivation automatique de la couleur d'accent communale.

Exigence de docs/spec.md et docs/design.md : la commune choisit une
teinte (CIVIC_ACCENT_COLOR), le système génère des variantes conformes
RGAA ; la teinte brute n'est jamais employée pour du texte ni un
composant porteur d'information.

Règles :
- accent-ink (liens, textes accentués) : ≥ 4,5:1 sur papier et carte ;
- accent (fond des boutons) : texte blanc ou encre imposé à ≥ 4,5:1,
  et ≥ 3:1 contre le papier (composant d'interface) ;
- accent-surface : mélange léger avec le papier (zones actives).
"""

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.http import require_GET

PAPER = "#F7F6F2"
CARD = "#FFFFFF"
DARK_PAPER = "#15171B"
DARK_CARD = "#1E2126"
INK = "#1D2129"
WHITE = "#FFFFFF"


def _rgb(color: str) -> tuple[float, float, float]:
    color = color.lstrip("#")
    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def _hex(rgb) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c))):02X}" for c in rgb)


def _luminance(color: str) -> float:
    def channel(value):
        value /= 255
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4

    r, g, b = (channel(c) for c in _rgb(color))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(color_a: str, color_b: str) -> float:
    la, lb = sorted([_luminance(color_a), _luminance(color_b)], reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _scale(color: str, factor: float) -> str:
    """factor < 1 : assombrit ; factor > 1 : éclaircit vers le blanc."""
    rgb = _rgb(color)
    if factor <= 1:
        return _hex(tuple(c * factor for c in rgb))
    amount = factor - 1
    return _hex(tuple(c + (255 - c) * amount for c in rgb))


def _adjust_until(color: str, backgrounds: list[str], ratio: float, darken: bool) -> str:
    candidate = color
    for step in range(1, 40):
        if all(contrast(candidate, bg) >= ratio for bg in backgrounds):
            return candidate
        factor = 1 - 0.04 * step if darken else 1 + 0.04 * step
        candidate = _scale(color, factor)
    return "#1D2129" if darken else "#E7E5E0"


def _mix(color_a: str, color_b: str, amount: float) -> str:
    ra = _rgb(color_a)
    rb = _rgb(color_b)
    return _hex(tuple(a * amount + b * (1 - amount) for a, b in zip(ra, rb, strict=True)))


def derive(accent: str) -> dict:
    """Variantes claires et sombres, toutes contrôlées en contraste."""
    accent_ink = _adjust_until(accent, [PAPER, CARD], 4.5, darken=True)
    # Bouton : 3:1 contre le papier, puis assombri jusqu'à ce que le
    # texte blanc tienne 4,5:1 (assombrir améliore les deux ratios).
    button = _adjust_until(accent, [PAPER], 3.0, darken=True)
    for step in range(1, 40):
        if contrast(WHITE, button) >= 4.5:
            break
        button = _scale(button, 1 - 0.04 * step)
    button_text = WHITE if contrast(WHITE, button) >= 4.5 else INK
    dark_ink = _adjust_until(accent, [DARK_PAPER, DARK_CARD], 4.5, darken=False)
    return {
        "accent": button,
        "accent_text": button_text,
        "accent_ink": accent_ink,
        "accent_surface": _mix(accent, PAPER, 0.12),
        "dark_accent_ink": dark_ink,
        "dark_accent_surface": _mix(accent, DARK_PAPER, 0.18),
    }


@require_GET
def theme_css(request):
    tokens = derive(settings.CIVIC["ACCENT_COLOR"])
    css = f""":root {{
  --accent: {tokens["accent"]};
  --accent-text: {tokens["accent_text"]};
  --accent-ink: {tokens["accent_ink"]};
  --accent-surface: {tokens["accent_surface"]};
}}
.btn-primary {{ color: {tokens["accent_text"]}; }}
@media (prefers-color-scheme: dark) {{
  :root {{
    --accent-ink: {tokens["dark_accent_ink"]};
    --accent-surface: {tokens["dark_accent_surface"]};
  }}
}}
"""
    response = HttpResponse(css, content_type="text/css")
    response["Cache-Control"] = "public, max-age=3600"
    return response
