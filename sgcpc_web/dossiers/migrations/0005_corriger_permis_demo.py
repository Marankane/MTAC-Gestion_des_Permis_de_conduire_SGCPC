from django.db import migrations


def corriger_permis_demo(apps, schema_editor):
    conducteur_model = apps.get_model("dossiers", "Conducteur")
    conducteur_model.objects.filter(
        numero_permis="NY90228247", mention_permis="APN403850"
    ).update(numero_permis="NY9028247")


def annuler_correction(apps, schema_editor):
    conducteur_model = apps.get_model("dossiers", "Conducteur")
    conducteur_model.objects.filter(
        numero_permis="NY9028247", mention_permis="APN403850"
    ).update(numero_permis="NY90228247")


class Migration(migrations.Migration):
    dependencies = [("dossiers", "0004_donnees_demo")]

    operations = [
        migrations.RunPython(corriger_permis_demo, annuler_correction),
    ]