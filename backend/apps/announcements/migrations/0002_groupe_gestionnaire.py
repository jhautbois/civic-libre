"""Crée le groupe « gestionnaire » avec les droits sur les annonces.

Les rôles du produit (docs/architecture.md) : agent (signalements de
son service), gestionnaire (annonces, modération), admin (superuser
Django). Les droits signalements s'ajouteront au lot 4.
"""

from django.db import migrations


def create_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    # Les permissions par défaut sont créées par un signal post_migrate,
    # APRÈS les migrations : il faut donc les créer explicitement ici.
    content_type, _ = ContentType.objects.get_or_create(
        app_label="announcements", model="announcement"
    )
    group, _ = Group.objects.get_or_create(name="gestionnaire")
    for action in ["view", "add", "change", "delete"]:
        permission, _ = Permission.objects.get_or_create(
            codename=f"{action}_announcement",
            content_type=content_type,
            defaults={"name": f"Can {action} annonce"},
        )
        group.permissions.add(permission)


def remove_group(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="gestionnaire").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("announcements", "0001_initial"),
        ("auth", "0012_alter_user_first_name_max_length"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]

    operations = [migrations.RunPython(create_group, remove_group)]
