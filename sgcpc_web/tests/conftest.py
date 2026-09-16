"""Fixtures partagées pour toute la suite de tests SGCPC."""

import pytest
from rest_framework.test import APIClient

from comptes.models import Role, Utilisateur


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def agent(db):
    return Utilisateur.objects.create_user(
        "agent1", password="Agent2026!", role=Role.AGENT_POLICE,
        first_name="Issoufou", last_name="Moussa",
    )


@pytest.fixture
def verificateur(db):
    return Utilisateur.objects.create_user(
        "verif1", password="Verif2026!", role=Role.ADMIN_REGIONAL,
        first_name="Aicha", last_name="Garba",
    )


@pytest.fixture
def president_commission(db):
    return Utilisateur.objects.create_user(
        "president1", password="Pres2026!", role=Role.MEMBRE_COMMISSION,
        first_name="Boubacar", last_name="Sani",
    )


@pytest.fixture
def admin_systeme(db):
    return Utilisateur.objects.create_superuser(
        "admin", "admin@sgcpc.ne", "AdminSGCPC2026!", role=Role.ADMIN_SYSTEME,
    )


@pytest.fixture
def payload_dossier():
    """Payload valide pour POST /api/v1/dossiers/ (Module 1)."""
    return {
        "date_incident": "2026-09-06T14:30:00Z",
        "ville": "Niamey",
        "quartier": "Plateau",
        "type_incident": "CORPOREL",
        "alcool": True,
        "vitesse_excessive": False,
        "autres_circonstances": "Choc frontal, route mouillée",
        "nombre_blesses": 2,
        "nombre_deces": 0,
        "gravite": "Moyenne",
        "conducteur": {
            "nom": "Souley", "prenom": "Amadou", "date_naissance": "1988-04-15",
            "lieu_naissance": "Niamey",
            "numero_permis": "NE-5551234", "telephone": "+22796000000",
            "mention_permis": "Nationale",
            "type_permis": "BC",
            "email": "", "adresse": "Niamey",
        },
        "vehicule": {
            "marque": "Toyota", "modele": "Corolla", "plaque": "1122-NG", "type_vehicule": "VOITURE",
        },
    }
