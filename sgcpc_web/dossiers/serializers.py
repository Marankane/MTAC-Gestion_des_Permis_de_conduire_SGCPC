from rest_framework import serializers

from .models import Conducteur, Vehicule, Dossier, PieceJointe, HistoriqueDossier, StatutDossier


class ConducteurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conducteur
        fields = [
            "id", "code_qr", "nom", "prenom", "date_naissance", "lieu_naissance",
            "numero_permis", "mention_permis", "type_permis", "statut_permis",
            "date_delivrance", "date_expiration", "date_suspension", "telephone", "email", "adresse",
        ]
        extra_kwargs = {
            # Le champ est bien unique en base, mais DRF ajoute par défaut un
            # UniqueValidator qui interdirait toute resoumission d'un permis déjà
            # connu. Ce cas est volontaire (cf. DossierCreateSerializer.create) :
            # un conducteur avec un accident supplémentaire doit pouvoir être
            # rattaché à un nouveau dossier sans être bloqué à la validation.
            "numero_permis": {"validators": []},
            "mention_permis": {"validators": []},
        }
        read_only_fields = ["id", "code_qr"]
        validators = []


class VehiculeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicule
        fields = ["id", "marque", "modele", "plaque", "type_vehicule"]


class PieceJointeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PieceJointe
        fields = ["id", "type_piece", "fichier", "uploade_le"]
        read_only_fields = ["uploade_le"]


class HistoriqueDossierSerializer(serializers.ModelSerializer):
    utilisateur_nom = serializers.CharField(source="utilisateur.__str__", read_only=True)

    class Meta:
        model = HistoriqueDossier
        fields = ["id", "action", "utilisateur_nom", "date_action", "details"]


class DossierListSerializer(serializers.ModelSerializer):
    """Version allégée pour les listes (tableau de bord mobile/web)."""

    conducteur_nom = serializers.CharField(source="conducteur.__str__", read_only=True)
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    type_incident_display = serializers.CharField(source="get_type_incident_display", read_only=True)

    class Meta:
        model = Dossier
        fields = [
            "id", "uuid", "numero", "conducteur_nom", "type_incident_display",
            "date_incident", "ville", "statut", "statut_display", "en_retard",
        ]


class DossierDetailSerializer(serializers.ModelSerializer):
    """Vue complète en lecture, avec sous-objets imbriqués."""

    conducteur = ConducteurSerializer(read_only=True)
    vehicule = VehiculeSerializer(read_only=True)
    pieces = PieceJointeSerializer(many=True, read_only=True)
    historique = HistoriqueDossierSerializer(many=True, read_only=True)
    statut_display = serializers.CharField(source="get_statut_display", read_only=True)
    type_incident_display = serializers.CharField(source="get_type_incident_display", read_only=True)
    agent_saisisseur_nom = serializers.CharField(source="agent_saisisseur.__str__", read_only=True)

    class Meta:
        model = Dossier
        fields = [
            "id", "uuid", "numero", "date_incident", "ville", "quartier", "latitude", "longitude",
            "type_incident", "type_incident_display", "vitesse_excessive", "alcool", "stupefiants",
            "feu_rouge", "autres_circonstances", "nombre_blesses", "nombre_deces", "gravite",
            "date_saisie", "statut", "statut_display", "motif_rejet", "en_retard",
            "modifiable_librement", "agent_saisisseur_nom", "conducteur", "vehicule", "pieces", "historique",
        ]
        read_only_fields = [f for f in fields if f not in ()]


class DossierCreateSerializer(serializers.ModelSerializer):
    """Création depuis le terrain (mobile) : conducteur/véhicule imbriqués (créés à la volée),
    pour permettre une saisie en un seul appel, y compris hors-ligne puis synchronisé."""

    conducteur = ConducteurSerializer()
    vehicule = VehiculeSerializer()

    class Meta:
        model = Dossier
        fields = [
            "date_incident", "ville", "quartier", "latitude", "longitude", "type_incident",
            "vitesse_excessive", "alcool", "stupefiants", "feu_rouge", "autres_circonstances",
            "nombre_blesses", "nombre_deces", "gravite", "conducteur", "vehicule",
        ]

    def create(self, validated_data):
        conducteur_data = validated_data.pop("conducteur")
        vehicule_data = validated_data.pop("vehicule")

        # Réutilise le conducteur s'il existe déjà (numéro de permis unique)
        conducteur, _ = Conducteur.objects.update_or_create(
            numero_permis=conducteur_data["numero_permis"],
            mention_permis=conducteur_data["mention_permis"],
            defaults=conducteur_data,
        )
        vehicule = Vehicule.objects.create(**vehicule_data)

        dossier = Dossier.objects.create(
            conducteur=conducteur,
            vehicule=vehicule,
            agent_saisisseur=self.context["request"].user,
            **validated_data,
        )

        HistoriqueDossier.objects.create(
            dossier=dossier,
            utilisateur=self.context["request"].user,
            action="Création du dossier (via app mobile)",
        )

        from .utils import generer_bordereau_pdf
        from .models import TypePiece

        bordereau = generer_bordereau_pdf(dossier)
        PieceJointe.objects.create(dossier=dossier, type_piece=TypePiece.AUTRE, fichier=bordereau)

        return dossier

    def to_representation(self, instance):
        return DossierDetailSerializer(instance, context=self.context).data


class VerificationActionSerializer(serializers.Serializer):
    """Payload pour valider/rejeter/demander un complément (Module 2)."""

    motif = serializers.CharField(required=False, allow_blank=True)
