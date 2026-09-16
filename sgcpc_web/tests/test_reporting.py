"""Tests du Module 7 (statistiques, alertes, exports)."""

import pytest
from datetime import timedelta
from django.utils import timezone

from dossiers.models import Dossier, Conducteur, Vehicule, TypeIncident, TypeVehicule, StatutDossier
from commissions.models import SessionCommission, Convocation
from reporting_stats import services


@pytest.fixture
def dossier_ancien_non_decide(agent, db):
    """Dossier vieux de 40 jours, toujours en instruction => doit remonter en alerte."""
    conducteur = Conducteur.objects.create(
        nom="Retard", prenom="Test", date_naissance="1990-01-01",
        numero_permis="NE-RETARD1", telephone="+22790000000",
    )
    vehicule = Vehicule.objects.create(marque="X", modele="Y", plaque="RETARD-1", type_vehicule=TypeVehicule.VOITURE)
    dossier = Dossier.objects.create(
        agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
        type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
    )
    Dossier.objects.filter(pk=dossier.pk).update(date_saisie=timezone.now() - timedelta(days=40))
    dossier.refresh_from_db()
    return dossier


@pytest.mark.django_db
class TestAlertes:
    def test_dossier_en_retard_detecte(self, dossier_ancien_non_decide):
        resultat = services.alertes()
        assert resultat["nb_dossiers_en_retard"] == 1

    def test_dossier_recent_non_detecte(self, agent):
        conducteur = Conducteur.objects.create(
            nom="Recent", prenom="Test", date_naissance="1990-01-01",
            numero_permis="NE-RECENT1", telephone="+22790000000",
        )
        vehicule = Vehicule.objects.create(marque="X", modele="Y", plaque="RECENT-1", type_vehicule=TypeVehicule.VOITURE)
        Dossier.objects.create(
            agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
            type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
        )
        resultat = services.alertes()
        assert resultat["nb_dossiers_en_retard"] == 0

    def test_session_surbookee_detectee(self, president_commission, agent):
        session = SessionCommission.objects.create(
            date_session=timezone.now() + timedelta(days=10), lieu="Niamey",
            capacite=1, president=president_commission,
        )
        for i in range(2):
            conducteur = Conducteur.objects.create(
                nom=f"C{i}", prenom="T", date_naissance="1990-01-01",
                numero_permis=f"NE-SB{i}", telephone="+22790000000",
            )
            vehicule = Vehicule.objects.create(marque="X", modele="Y", plaque=f"SB-{i}", type_vehicule=TypeVehicule.VOITURE)
            dossier = Dossier.objects.create(
                agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
                type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
                statut=StatutDossier.VERIFIE,
            )
            Convocation.objects.create(dossier=dossier, session=session)

        resultat = services.alertes()
        assert resultat["nb_sessions_surbookees"] == 1

    def test_session_non_surbookee_non_detectee(self, president_commission, agent):
        session = SessionCommission.objects.create(
            date_session=timezone.now() + timedelta(days=10), lieu="Niamey",
            capacite=10, president=president_commission,
        )
        conducteur = Conducteur.objects.create(
            nom="OK", prenom="T", date_naissance="1990-01-01",
            numero_permis="NE-OK1", telephone="+22790000000",
        )
        vehicule = Vehicule.objects.create(marque="X", modele="Y", plaque="OK-1", type_vehicule=TypeVehicule.VOITURE)
        dossier = Dossier.objects.create(
            agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
            type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
            statut=StatutDossier.VERIFIE,
        )
        Convocation.objects.create(dossier=dossier, session=session)

        resultat = services.alertes()
        assert resultat["nb_sessions_surbookees"] == 0


@pytest.mark.django_db
class TestExports:
    def test_dashboard_accessible_authentifie(self, client, admin_systeme):
        client.force_login(admin_systeme)
        response = client.get("/stats/")
        assert response.status_code == 200

    def test_dashboard_refuse_anonyme(self, client):
        response = client.get("/stats/")
        assert response.status_code == 302  # redirection vers la connexion

    def test_export_csv_encodage_utf8(self, client, admin_systeme, agent):
        """Régression : les accents ne doivent pas être corrompus (bug corrigé)."""
        conducteur = Conducteur.objects.create(
            nom="Détenteur", prenom="Éric", date_naissance="1990-01-01",
            numero_permis="NE-UTF8", telephone="+22790000000",
        )
        vehicule = Vehicule.objects.create(marque="X", modele="Y", plaque="UTF-1", type_vehicule=TypeVehicule.VOITURE)
        Dossier.objects.create(
            agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
            type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
        )
        client.force_login(admin_systeme)
        response = client.get("/stats/export/csv/")
        contenu = response.content.decode("utf-8-sig")
        assert "Détenteur" in contenu
        assert "Éric" in contenu
        assert "Numéro" in contenu.splitlines()[0]

    def test_export_pdf_genere(self, client, admin_systeme):
        client.force_login(admin_systeme)
        response = client.get("/stats/export/pdf/")
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"


@pytest.mark.django_db
class TestStatsAPI:
    def test_tableau_de_bord_api(self, api_client, admin_systeme):
        api_client.force_authenticate(user=admin_systeme)
        response = api_client.get("/api/v1/stats/tableau-de-bord/")
        assert response.status_code == 200
        for cle in ["resume", "par_mois", "par_region", "decisions", "delais", "presence_commissions"]:
            assert cle in response.data

    def test_alertes_api_refuse_anonyme(self, api_client):
        response = api_client.get("/api/v1/stats/alertes/")
        assert response.status_code == 401
