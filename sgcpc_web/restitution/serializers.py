from rest_framework import serializers

from .models import Restitution


class RestitutionSerializer(serializers.ModelSerializer):
    dossier_numero = serializers.CharField(source="decision.audition.convocation.dossier.numero", read_only=True)
    conducteur_nom = serializers.CharField(
        source="decision.audition.convocation.dossier.conducteur.__str__", read_only=True
    )
    effectuee = serializers.BooleanField(read_only=True)

    class Meta:
        model = Restitution
        fields = [
            "id", "decision", "dossier_numero", "conducteur_nom", "date_remise",
            "remis_par", "piece_identite_verifiee", "rappel_envoye", "effectuee",
        ]
        read_only_fields = ["date_remise", "remis_par"]
