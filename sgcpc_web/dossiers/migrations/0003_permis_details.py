from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("dossiers", "0002_permis_fields")]

    operations = [
        migrations.AddField(model_name="conducteur", name="lieu_naissance", field=models.CharField(blank=True, max_length=150)),
        migrations.AddField(
            model_name="conducteur", name="statut_permis",
            field=models.CharField(choices=[("ACTIF", "Actif"), ("SUSPENDU", "Suspendu"), ("EXPIRE", "Expire"), ("RETIRE", "Retiré")], default="ACTIF", max_length=10),
        ),
        migrations.AddField(model_name="conducteur", name="date_delivrance", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="conducteur", name="date_expiration", field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name="conducteur", name="date_suspension", field=models.DateField(blank=True, null=True)),
    ]