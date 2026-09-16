import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dossiers", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="conducteur",
            name="code_qr",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AddField(
            model_name="conducteur",
            name="mention_permis",
            field=models.CharField(default="Nationale", max_length=100),
        ),
        migrations.AddField(
            model_name="conducteur",
            name="type_permis",
            field=models.CharField(
                choices=[("A", "A"), ("BC", "BC"), ("D", "D"), ("E", "E"), ("F", "F")],
                default="A",
                max_length=2,
            ),
        ),
        migrations.AlterField(
            model_name="conducteur",
            name="numero_permis",
            field=models.CharField(max_length=50),
        ),
        migrations.AddConstraint(
            model_name="conducteur",
            constraint=models.UniqueConstraint(
                fields=("numero_permis", "mention_permis"),
                name="unique_numero_mention_permis",
            ),
        ),
    ]