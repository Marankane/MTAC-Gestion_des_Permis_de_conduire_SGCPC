"""Test d'intégration bout-en-bout : reproduit le workflow réel des 7 étapes
du CDCF, entièrement via l'API REST (comme le ferait l'app mobile + le web)."""

import pytest

from dossiers.models import Dossier, StatutDossier
from commissions.models import SessionCommission, Convocation
from decisions.models import Decision
from restitution.models import Restitution


@pytest.mark.django_db
class TestWorkflowCompletModules1a5:
    def test_workflow_saisie_a_restitution(
        self, api_client, agent, verificateur, president_commission, payload_dossier
    ):
        # 1. Saisie du dossier (Module 1)
        api_client.force_authenticate(user=agent)
        r = api_client.post("/api/v1/dossiers/", payload_dossier, format="json")
        assert r.status_code == 201
        dossier_id = r.data["id"]

        # 2. Vérification (Module 2)
        api_client.force_authenticate(user=verificateur)
        r = api_client.post(f"/api/v1/dossiers/{dossier_id}/valider/")
        assert r.status_code == 200
        assert Dossier.objects.get(pk=dossier_id).statut == StatutDossier.VERIFIE

        # 3. Création de la session de commission (Module 3)
        api_client.force_authenticate(user=president_commission)
        r = api_client.post(
            "/api/v1/commissions/sessions/",
            {
                "date_session": "2026-09-25T09:00:00Z",
                "lieu": "Salle de la Direction Régionale, Niamey",
                "capacite": 10,
                "president": president_commission.id,
                "membres": [],
            },
            format="json",
        )
        assert r.status_code == 201
        session_id = r.data["id"]

        # 4. Programmation du dossier dans la session
        r = api_client.post(f"/api/v1/commissions/sessions/{session_id}/programmer/{dossier_id}/")
        assert r.status_code == 201
        convocation_id = r.data["id"]
        assert Dossier.objects.get(pk=dossier_id).statut == StatutDossier.PROGRAMME
        assert Convocation.objects.get(pk=convocation_id).lettre_pdf  # PDF généré

        # 5. Marquer présent + Audition (Module 4)
        r = api_client.post(f"/api/v1/commissions/convocations/{convocation_id}/presence/", {"statut": "present"}, format="json")
        assert r.status_code == 200

        r = api_client.post(
            "/api/v1/commissions/auditions/",
            {"convocation": convocation_id, "explications_conducteur": "Route mouillée."},
            format="json",
        )
        assert r.status_code == 201
        audition_id = r.data["id"]

        # 6. Décision : suspension de 6 mois
        r = api_client.post(
            "/api/v1/decisions/",
            {
                "audition": audition_id, "type_decision": "SUSPENSION",
                "duree_suspension_mois": 6, "motivation": "Conduite dangereuse avérée.",
            },
            format="json",
        )
        assert r.status_code == 201
        decision_id = r.data["id"]
        assert Dossier.objects.get(pk=dossier_id).statut == StatutDossier.DECIDE
        assert r.data["date_fin_suspension"] is not None

        decision = Decision.objects.get(pk=decision_id)
        assert decision.arrete_pdf  # PDF généré automatiquement

        # Une restitution doit avoir été créée automatiquement (suspension => restitution différée)
        restitution = Restitution.objects.get(decision=decision)
        assert restitution.date_remise is None

        # 7. Restitution (Module 5) et clôture
        r = api_client.post(
            f"/api/v1/restitutions/{restitution.pk}/restituer/",
            {"piece_identite_verifiee": True},
            format="json",
        )
        assert r.status_code == 200
        dossier_final = Dossier.objects.get(pk=dossier_id)
        assert dossier_final.statut == StatutDossier.CLOTURE

        # Historique complet conservé (traçabilité CDCF)
        assert dossier_final.historique.count() >= 4

    def test_retrait_definitif_transmet_au_tribunal(
        self, api_client, agent, verificateur, president_commission, payload_dossier
    ):
        """CDCF 3.4 : un retrait définitif doit être transmis au tribunal pour homologation."""
        api_client.force_authenticate(user=agent)
        dossier_id = api_client.post("/api/v1/dossiers/", payload_dossier, format="json").data["id"]

        api_client.force_authenticate(user=verificateur)
        api_client.post(f"/api/v1/dossiers/{dossier_id}/valider/")

        api_client.force_authenticate(user=president_commission)
        session_id = api_client.post(
            "/api/v1/commissions/sessions/",
            {"date_session": "2026-10-01T09:00:00Z", "lieu": "Niamey", "capacite": 5,
             "president": president_commission.id, "membres": []},
            format="json",
        ).data["id"]
        convocation_id = api_client.post(f"/api/v1/commissions/sessions/{session_id}/programmer/{dossier_id}/").data["id"]
        audition_id = api_client.post(
            "/api/v1/commissions/auditions/",
            {"convocation": convocation_id, "explications_conducteur": "Récidive."},
            format="json",
        ).data["id"]

        r = api_client.post(
            "/api/v1/decisions/",
            {"audition": audition_id, "type_decision": "RETRAIT_DEFINITIF", "motivation": "Récidive grave."},
            format="json",
        )
        assert r.status_code == 201
        decision = Decision.objects.get(pk=r.data["id"])
        assert decision.transmis_tribunal is True
        # Un retrait définitif ne doit PAS générer d'enregistrement de restitution
        assert not Restitution.objects.filter(decision=decision).exists()

    def test_non_membre_commission_ne_peut_pas_decider(
        self, api_client, agent, verificateur, president_commission, payload_dossier
    ):
        """RBAC : seul un membre de commission peut rendre une décision."""
        api_client.force_authenticate(user=agent)
        dossier_id = api_client.post("/api/v1/dossiers/", payload_dossier, format="json").data["id"]
        api_client.force_authenticate(user=verificateur)
        api_client.post(f"/api/v1/dossiers/{dossier_id}/valider/")

        api_client.force_authenticate(user=president_commission)
        session_id = api_client.post(
            "/api/v1/commissions/sessions/",
            {"date_session": "2026-10-01T09:00:00Z", "lieu": "Niamey", "capacite": 5,
             "president": president_commission.id, "membres": []},
            format="json",
        ).data["id"]
        convocation_id = api_client.post(f"/api/v1/commissions/sessions/{session_id}/programmer/{dossier_id}/").data["id"]
        audition_id = api_client.post(
            "/api/v1/commissions/auditions/",
            {"convocation": convocation_id, "explications_conducteur": "..."},
            format="json",
        ).data["id"]

        # Un agent de police (pas commission) tente de décider
        api_client.force_authenticate(user=agent)
        r = api_client.post(
            "/api/v1/decisions/",
            {"audition": audition_id, "type_decision": "RELAXE", "motivation": "..."},
            format="json",
        )
        assert r.status_code == 403

    def test_lecture_decision_ouverte_a_tout_authentifie(
        self, api_client, agent, verificateur, president_commission, payload_dossier
    ):
        """Régression : la lecture (téléchargement arrêté PDF) ne doit pas être bloquée
        pour les non-membres de commission (bug corrigé lors des tests manuels)."""
        api_client.force_authenticate(user=agent)
        dossier_id = api_client.post("/api/v1/dossiers/", payload_dossier, format="json").data["id"]
        api_client.force_authenticate(user=verificateur)
        api_client.post(f"/api/v1/dossiers/{dossier_id}/valider/")

        api_client.force_authenticate(user=president_commission)
        session_id = api_client.post(
            "/api/v1/commissions/sessions/",
            {"date_session": "2026-10-01T09:00:00Z", "lieu": "Niamey", "capacite": 5,
             "president": president_commission.id, "membres": []},
            format="json",
        ).data["id"]
        convocation_id = api_client.post(f"/api/v1/commissions/sessions/{session_id}/programmer/{dossier_id}/").data["id"]
        audition_id = api_client.post(
            "/api/v1/commissions/auditions/",
            {"convocation": convocation_id, "explications_conducteur": "..."},
            format="json",
        ).data["id"]
        decision_id = api_client.post(
            "/api/v1/decisions/",
            {"audition": audition_id, "type_decision": "RELAXE", "motivation": "Aucune faute retenue."},
            format="json",
        ).data["id"]

        # L'agent (non-commission) doit pouvoir LIRE la décision et son PDF
        api_client.force_authenticate(user=agent)
        assert api_client.get(f"/api/v1/decisions/{decision_id}/").status_code == 200
        r = api_client.get(f"/api/v1/decisions/{decision_id}/arrete_pdf/")
        assert r.status_code == 200
        assert r["Content-Type"] == "application/pdf"
