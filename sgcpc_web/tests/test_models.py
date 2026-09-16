"""Tests des règles métier portées par les modèles (délais, calculs, etc.)."""

import pytest
from datetime import timedelta
from django.utils import timezone

from dossiers.models import Dossier, Conducteur, Vehicule, StatutDossier, TypeIncident, TypeVehicule
from comptes.models import Role, Utilisateur


@pytest.fixture
def conducteur(db):
    return Conducteur.objects.create(
        nom="Test", prenom="Test", date_naissance="1990-01-01",
        numero_permis="NE-0000001", telephone="+22790000000",
    )


@pytest.fixture
def vehicule(db):
    return Vehicule.objects.create(marque="Toyota", modele="Hilux", plaque="TEST-01", type_vehicule=TypeVehicule.VOITURE)


@pytest.mark.django_db
class TestNumerotationDossier:
    def test_premier_numero_de_lannee(self, agent, conducteur, vehicule):
        dossier = Dossier.objects.create(
            agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
            type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
        )
        annee = timezone.now().year
        assert dossier.numero == f"Niger-{annee}-000001"

    def test_numeros_incrementaux(self, agent, conducteur, vehicule):
        """Le CDCF exige un numéro unique et séquentiel par année (ex: Niger-2026-000123)."""
        vehicule2 = Vehicule.objects.create(marque="X", modele="Y", plaque="TEST-02", type_vehicule=TypeVehicule.VOITURE)
        conducteur2 = Conducteur.objects.create(
            nom="Test2", prenom="Test2", date_naissance="1990-01-01",
            numero_permis="NE-0000002", telephone="+22790000001",
        )
        d1 = Dossier.objects.create(
            agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
            type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
        )
        d2 = Dossier.objects.create(
            agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
            type_incident=TypeIncident.MATERIEL, conducteur=conducteur2, vehicule=vehicule2,
        )
        assert d1.numero.endswith("000001")
        assert d2.numero.endswith("000002")


@pytest.mark.django_db
class TestDelaisMetier:
    def test_modifiable_librement_dans_les_24h(self, agent, conducteur, vehicule):
        """CDCF 3.1 : un dossier ne peut être modifié librement que dans les 24h après saisie."""
        dossier = Dossier.objects.create(
            agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
            type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
        )
        assert dossier.modifiable_librement is True

    def test_non_modifiable_apres_24h(self, agent, conducteur, vehicule):
        dossier = Dossier.objects.create(
            agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
            type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
        )
        Dossier.objects.filter(pk=dossier.pk).update(date_saisie=timezone.now() - timedelta(hours=25))
        dossier.refresh_from_db()
        assert dossier.modifiable_librement is False

    def test_pas_en_retard_si_recent(self, agent, conducteur, vehicule):
        dossier = Dossier.objects.create(
            agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
            type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
        )
        assert dossier.en_retard is False

    def test_en_retard_apres_30_jours_sans_decision(self, agent, conducteur, vehicule):
        """CDCF 3.7 : alerte si un dossier dépasse 30 jours sans décision."""
        dossier = Dossier.objects.create(
            agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
            type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
        )
        Dossier.objects.filter(pk=dossier.pk).update(date_saisie=timezone.now() - timedelta(days=31))
        dossier.refresh_from_db()
        assert dossier.en_retard is True

    def test_pas_en_retard_si_deja_cloture(self, agent, conducteur, vehicule):
        """Un dossier vieux mais déjà clôturé n'est pas une alerte."""
        dossier = Dossier.objects.create(
            agent_saisisseur=agent, date_incident=timezone.now(), ville="Niamey",
            type_incident=TypeIncident.CORPOREL, conducteur=conducteur, vehicule=vehicule,
            statut=StatutDossier.CLOTURE,
        )
        Dossier.objects.filter(pk=dossier.pk).update(date_saisie=timezone.now() - timedelta(days=60))
        dossier.refresh_from_db()
        assert dossier.en_retard is False


@pytest.mark.django_db
class TestRolesUtilisateur:
    def test_agent_police_est_force_de_lordre(self):
        u = Utilisateur.objects.create_user("a", password="x", role=Role.AGENT_POLICE)
        assert u.is_force_ordre() is True
        assert u.is_commission() is False

    def test_membre_commission_nest_pas_force_de_lordre(self):
        u = Utilisateur.objects.create_user("b", password="x", role=Role.MEMBRE_COMMISSION)
        assert u.is_force_ordre() is False
        assert u.is_commission() is True
