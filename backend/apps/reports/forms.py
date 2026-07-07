from django import forms

from .models import Category


class ReportForm(forms.Form):
    category = forms.ModelChoiceField(
        label="Que voulez-vous signaler ?",
        queryset=Category.objects.filter(is_active=True),
        widget=forms.RadioSelect,
        empty_label=None,
        error_messages={"required": "Choisissez une catégorie."},
    )
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput)
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput)
    address = forms.CharField(
        label="Adresse ou lieu-dit",
        required=False,
        max_length=300,
        widget=forms.TextInput(attrs={"autocomplete": "street-address", "placeholder": ""}),
        help_text="Facultatif si vous placez le point sur la carte.",
    )
    location_hint = forms.CharField(
        label="Précision sur l'emplacement",
        required=False,
        max_length=200,
        help_text="Par exemple : face au numéro 12, côté école.",
    )
    description = forms.CharField(
        label="Décrivez le problème",
        max_length=4000,
        widget=forms.Textarea(attrs={"rows": 4}),
        error_messages={"required": "Décrivez le problème en quelques mots."},
    )
    photo = forms.ImageField(
        label="Photo",
        required=False,
        help_text="Facultative. Cadrez le problème, évitez les personnes et les plaques.",
    )
    reporter_email = forms.EmailField(
        label="Votre courriel",
        required=False,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
        help_text="Facultatif : pour être informé de l'avancement. Jamais publié.",
    )
    # Pot de miel anti-robots : champ invisible qui doit rester vide.
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1"}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            raise forms.ValidationError("Envoi refusé.")
        lat, lon = cleaned.get("latitude"), cleaned.get("longitude")
        if (lat is None) != (lon is None):
            cleaned["latitude"] = cleaned["longitude"] = None
            lat = lon = None
        if lat is None and not (cleaned.get("address") or "").strip():
            self.add_error(
                "address",
                "Indiquez où se trouve le problème : sur la carte ou par une adresse.",
            )
        return cleaned
