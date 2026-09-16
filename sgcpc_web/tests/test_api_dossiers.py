"""Tests de l'API du Module 1 & 2 (saisie et vérification) — endpoints consommés
par l'app mobile Flutter et le futur portail citoyen."""

import pytest

from dossiers.models import Dossier, StatutDossier


@pytest.mark.django_db
class TestCreationDossier:
    def test_creation_par_agent_police(self, api_client, agent, payload_dossier):
        api_client.force_authenticate(user=agent)
        response = api_client.post("/api/v1/dossiers/", payload_dossier, format="json")

        assert response.status_code == 201
        assert response.data["numero"].startswith("Niger-")
        assert response.data["conducteur"]["numero_permis"] == "NE-5551234"
        assert Dossier.objects.count() == 1

    def test_conducteur_reutilise_si_permis_existant(self, api_client, agent, payload_dossier):
        """Un même conducteur (numéro de permis) ne doit pas être dupliqué en base."""
        api_client.force_authenticate(user=agent)
        api_client.post("/api/v1/dossiers/", payload_dossier, format="json")

        payload_dossier["ville"] = "Zinder"  # deuxième incident, même conducteur
        response = api_client.post("/api/v1/dossiers/", payload_dossier, format="json")

        assert response.status_code == 201
        from dossiers.models import Conducteur

        assert Conducteur.objects.filter(numero_permis="NE-5551234").count() == 1

    def test_numero_et_mention_identifient_le_permis(self, api_client, agent, payload_dossier):
        api_client.force_authenticate(user=agent)
        api_client.post("/api/v1/dossiers/", payload_dossier, format="json")

        autre_payload = {**payload_dossier, "ville": "Zinder"}
        autre_payload["conducteur"] = {
            **payload_dossier["conducteur"],
            "mention_permis": "Internationale",
        }
        response = api_client.post("/api/v1/dossiers/", autre_payload, format="json")

        assert response.status_code == 201
        from dossiers.models import Conducteur

        assert Conducteur.objects.filter(numero_permis="NE-5551234").count() == 2

    def test_bordereau_genere_automatiquement(self, api_client, agent, payload_dossier):
        api_client.force_authenticate(user=agent)
        response = api_client.post("/api/v1/dossiers/", payload_dossier, format="json")
        dossier = Dossier.objects.get(pk=response.data["id"])
        assert dossier.pieces.count() == 1

    def test_historique_trace_la_creation(self, api_client, agent, payload_dossier):
        api_client.force_authenticate(user=agent)
        response = api_client.post("/api/v1/dossiers/", payload_dossier, format="json")
        dossier = Dossier.objects.get(pk=response.data["id"])
        assert dossier.historique.count() == 1
        assert "Création" in dossier.historique.first().action

    def test_refuse_creation_par_non_force_de_lordre(self, api_client, verificateur, payload_dossier):
        """RBAC : seuls Police/Gendarmerie peuvent saisir un dossier (Module 1)."""
        api_client.force_authenticate(user=verificateur)
        response = api_client.post("/api/v1/dossiers/", payload_dossier, format="json")
        assert response.status_code == 403

    def test_refuse_creation_anonyme(self, api_client, payload_dossier):
        response = api_client.post("/api/v1/dossiers/", payload_dossier, format="json")
        assert response.status_code == 401

    def test_refuse_creation_donnees_invalides(self, api_client, agent, payload_dossier):
        payload_dossier["conducteur"]["numero_permis"] = ""  # champ requis manquant
        api_client.force_authenticate(user=agent)
        response = api_client.post("/api/v1/dossiers/", payload_dossier, format="json")
        assert response.status_code == 400


@pytest.mark.django_db
class TestListeEtVisibiliteDossiers:
    def test_agent_ne_voit_que_ses_propres_dossiers(self, api_client, agent, payload_dossier):
        """RBAC : un agent de terrain ne doit voir que les dossiers qu'il a saisis."""
        from comptes.models import Role, Utilisateur

        autre_agent = Utilisateur.objects.create_user("agent2", password="x", role=Role.AGENT_POLICE)

        api_client.force_authenticate(user=agent)
        api_client.post("/api/v1/dossiers/", payload_dossier, format="json")

        api_client.force_authenticate(user=autre_agent)
        response = api_client.get("/api/v1/dossiers/")
        assert response.data["count"] == 0

        api_client.force_authenticate(user=agent)
        response = api_client.get("/api/v1/dossiers/")
        assert response.data["count"] == 1

    def test_admin_regional_voit_tous_les_dossiers(self, api_client, agent, verificateur, payload_dossier):
        api_client.force_authenticate(user=agent)
        api_client.post("/api/v1/dossiers/", payload_dossier, format="json")

        api_client.force_authenticate(user=verificateur)
        response = api_client.get("/api/v1/dossiers/")
        assert response.data["count"] == 1


@pytest.mark.django_db
class TestVerificationDossier:
    def _creer_dossier(self, api_client, agent, payload_dossier):
        api_client.force_authenticate(user=agent)
        response = api_client.post("/api/v1/dossiers/", payload_dossier, format="json")
        return response.data["id"]

    def test_validation_par_admin_regional(self, api_client, agent, verificateur, payload_dossier):
        dossier_id = self._creer_dossier(api_client, agent, payload_dossier)

        api_client.force_authenticate(user=verificateur)
        response = api_client.post(f"/api/v1/dossiers/{dossier_id}/valider/")

        assert response.status_code == 200
        dossier = Dossier.objects.get(pk=dossier_id)
        assert dossier.statut == StatutDossier.VERIFIE
        assert dossier.verificateur == verificateur

    def test_agent_ne_peut_pas_valider(self, api_client, agent, payload_dossier):
        """RBAC : la validation (Module 2) est réservée à l'administration."""
        dossier_id = self._creer_dossier(api_client, agent, payload_dossier)
        response = api_client.post(f"/api/v1/dossiers/{dossier_id}/valider/")  # toujours authentifié comme agent
        assert response.status_code == 403

    def test_rejet_sans_motif_refuse(self, api_client, agent, verificateur, payload_dossier):
        """CDCF 3.2 : le motif de rejet est obligatoire."""
        dossier_id = self._creer_dossier(api_client, agent, payload_dossier)
        api_client.force_authenticate(user=verificateur)
        response = api_client.post(f"/api/v1/dossiers/{dossier_id}/rejeter/", {"motif": ""}, format="json")
        assert response.status_code == 400

    def test_rejet_avec_motif(self, api_client, agent, verificateur, payload_dossier):
        dossier_id = self._creer_dossier(api_client, agent, payload_dossier)
        api_client.force_authenticate(user=verificateur)
        response = api_client.post(
            f"/api/v1/dossiers/{dossier_id}/rejeter/", {"motif": "Pièces illisibles"}, format="json"
        )
        assert response.status_code == 200
        dossier = Dossier.objects.get(pk=dossier_id)
        assert dossier.statut == StatutDossier.REJETE
        assert dossier.motif_rejet == "Pièces illisibles"

    def test_bordereau_telechargeable_par_tout_authentifie(self, api_client, agent, payload_dossier):
        """La lecture (téléchargement) doit rester ouverte à tout utilisateur authentifié."""
        dossier_id = self._creer_dossier(api_client, agent, payload_dossier)
        response = api_client.get(f"/api/v1/dossiers/{dossier_id}/bordereau/")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
