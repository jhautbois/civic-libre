"""Groupe « agent » (traitement des signalements) et extension du
groupe « gestionnaire » aux signalements (modération comprise).

Les permissions sont créées explicitement : le signal post_migrate ne
les fournit qu'après la fin des migrations.
"""

from django.db import migrations

REPORT_PERMS = [
    ("view", "report", "signalement"),
    ("change", "report", "signalement"),
    ("view", "reportphoto", "photo de signalement"),
    ("change", "reportphoto", "photo de signalement"),
]


def create_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Permission = apps.get_model("auth", "Permission")
    ContentType = apps.get_model("contenttypes", "ContentType")

    agent, _ = Group.objects.get_or_create(name="agent")
    gestionnaire, _ = Group.objects.get_or_create(name="gestionnaire")

    for action, model, label in REPORT_PERMS:
        content_type, _ = ContentType.objects.get_or_create(app_label="reports", model=model)
        permission, _ = Permission.objects.get_or_create(
            codename=f"{action}_{model}",
            content_type=content_type,
            defaults={"name": f"Can {action} {label}"},
        )
        agent.permissions.add(permission)
        gestionnaire.permissions.add(permission)


def remove_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name="agent").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0003_reportupdate"),
        ("announcements", "0002_groupe_gestionnaire"),
        ("contenttypes", "0002_remove_content_type_name"),
    ]
    operations = [migrations.RunPython(create_groups, remove_groups)]
