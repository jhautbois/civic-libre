"""Catégories de signalement par défaut, modifiables ensuite dans l'admin.

Codes stables : ils servent de service_code Open311 et ne doivent plus
changer une fois l'instance en service.
"""

from django.db import migrations

DEFAULTS = [
    ("voirie", "Voirie et chaussée", "Trous, affaissements, signalisation dégradée"),
    ("eclairage", "Éclairage public", "Lampadaire en panne ou clignotant"),
    ("proprete", "Propreté et dépôts sauvages", "Dépôts d'ordures, poubelles, tags"),
    ("espaces-verts", "Espaces verts", "Arbres, haies, aires de jeux"),
    ("eau", "Eau et assainissement", "Fuites, avaloirs bouchés"),
    ("mobilier", "Mobilier urbain", "Bancs, abribus, barrières dégradés"),
    ("autre", "Autre problème", "Tout ce qui ne rentre pas ailleurs"),
]


def create_defaults(apps, schema_editor):
    Department = apps.get_model("reports", "Department")
    Category = apps.get_model("reports", "Category")
    department, _ = Department.objects.get_or_create(name="Services techniques")
    for code, name, description in DEFAULTS:
        Category.objects.get_or_create(
            code=code,
            defaults={"name": name, "description": description, "department": department},
        )


def remove_defaults(apps, schema_editor):
    Category = apps.get_model("reports", "Category")
    Category.objects.filter(code__in=[c for c, _, _ in DEFAULTS]).delete()


class Migration(migrations.Migration):
    dependencies = [("reports", "0001_initial")]
    operations = [migrations.RunPython(create_defaults, remove_defaults)]
