from rest_framework import serializers

from .models import Decision


class DecisionSerializer(serializers.ModelSerializer):
    type_decision_display = serializers.CharField(source="get_type_decision_display", read_only=True)
    dossier_numero = serializers.CharField(source="audition.convocation.dossier.numero", read_only=True)
    date_fin_suspension = serializers.DateTimeField(read_only=True)
    delai_recours_expire = serializers.BooleanField(read_only=True)

    class Meta:
        model = Decision
        fields = [
            "id", "audition", "dossier_numero", "type_decision", "type_decision_display",
            "duree_suspension_mois", "motivation", "date_decision", "decide_par",
            "date_fin_suspension", "delai_recours_expire", "transmis_tribunal",
        ]
        read_only_fields = ["date_decision", "decide_par", "transmis_tribunal"]

    def validate(self, attrs):
        type_decision = attrs.get("type_decision")
        duree = attrs.get("duree_suspension_mois")
        if type_decision == "SUSPENSION" and not duree:
            raise serializers.ValidationError("La durée de suspension (mois) est obligatoire.")
        if type_decision == "SUSPENSION" and duree and not (1 <= duree <= 36):
            raise serializers.ValidationError("La durée de suspension doit être comprise entre 1 et 36 mois.")
        if not attrs.get("motivation"):
            raise serializers.ValidationError("La décision doit être motivée.")
        return attrs
