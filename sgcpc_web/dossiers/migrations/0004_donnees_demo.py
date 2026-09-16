from datetime import date

from django.contrib.auth.hashers import make_password
from django.db import migrations


def creer_donnees_demo(apps, schema_editor):
    utilisateur_model = apps.get_model("comptes", "Utilisateur")
    conducteur_model = apps.get_model("dossiers", "Conducteur")

    utilisateur, _ = utilisateur_model.objects.get_or_create(
        username="test1",
        defaults={
            "first_name": "Utilisateur",
            "last_name": "Test",
            "role": "AGENT_POLICE",
            "is_active": True,
        },
    )
    utilisateur.password = make_password("test1234")
    utilisateur.role = "AGENT_POLICE"
    utilisateur.is_active = True
    utilisateur.save(update_fields=["password", "role", "is_active"])

    conducteur_model.objects.get_or_create(
        numero_permis="NY90228247",
        mention_permis="APN403850",
        defaults={
            "nom": "Demo",
            "prenom": "Utilisateur",
            "date_naissance": date(1990, 1, 1),
            "lieu_naissance": "Niamey",
            "type_permis": "BC",
            "statut_permis": "ACTIF",
            "date_delivrance": date(2024, 1, 15),
            "date_expiration": date(2034, 1, 15),
            "telephone": "+22790000000",
            "email": "",
            "adresse": "Niamey",
        },
    )


def supprimer_donnees_demo(apps, schema_editor):
    utilisateur_model = apps.get_model("comptes", "Utilisateur")
    conducteur_model = apps.get_model("dossiers", "Conducteur")
    conducteur_model.objects.filter(
        numero_permis="NY90228247", mention_permis="APN403850"
    ).delete()
    utilisateur_model.objects.filter(username="test1").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("dossiers", "0003_permis_details"),
        ("comptes", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(creer_donnees_demo, supprimer_donnees_demo),
    ]
