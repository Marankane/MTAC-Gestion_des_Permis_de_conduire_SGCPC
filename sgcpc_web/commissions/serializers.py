from rest_framework import serializers

from dossiers.serializers import DossierListSerializer
from .models import SessionCommission, Convocation, Audition


class SessionCommissionSerializer(serializers.ModelSerializer):
    president_nom = serializers.CharField(source="president.__str__", read_only=True)
    nombre_dossiers_programmes = serializers.IntegerField(read_only=True)
    surbookee = serializers.BooleanField(read_only=True)

    class Meta:
        model = SessionCommission
        fields = [
            "id", "date_session", "lieu", "capacite", "president", "president_nom",
            "membres", "nombre_dossiers_programmes", "surbookee",
        ]


class ConvocationSerializer(serializers.ModelSerializer):
    dossier = DossierListSerializer(read_only=True)
    dossier_id = serializers.PrimaryKeyRelatedField(source="dossier", read_only=True)
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    delai_respecte = serializers.BooleanField(read_only=True)

    class Meta:
        model = Convocation
        fields = [
            "id", "dossier", "dossier_id", "session", "date_envoi", "statut", "statut_display",
            "delai_respecte", "envoye_sms", "envoye_email", "envoye_courrier",
        ]


class AuditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Audition
        fields = ["id", "convocation", "explications_conducteur", "pieces_supplementaires", "date_audition", "enregistre_par"]
        read_only_fields = ["date_audition", "enregistre_par"]
