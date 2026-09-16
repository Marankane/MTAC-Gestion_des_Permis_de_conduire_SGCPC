"""Permissions DRF basées sur les rôles métier (RBAC) du CDCF."""

from rest_framework.permissions import BasePermission

from .models import Role


class EstForceDeLOrdre(BasePermission):
    """Seuls Police/Gendarmerie peuvent saisir un nouvel accident (Module 1)."""

    message = "Seuls les agents de Police ou Gendarmerie peuvent saisir un dossier."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_force_ordre())


class EstAdminRegionalOuSysteme(BasePermission):
    """Vérification des dossiers (Module 2) réservée à l'administration."""

    message = "Seul un administrateur régional ou système peut vérifier un dossier."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (Role.ADMIN_REGIONAL, Role.ADMIN_SYSTEME)
        )


class EstMembreCommission(BasePermission):
    """Auditions et décisions réservées aux membres/secrétaires de commission."""

    message = "Seul un membre ou secrétaire de commission peut effectuer cette action."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_commission())


class LectureSeuleOuAuteur(BasePermission):
    """Un agent ne peut modifier que les dossiers qu'il a lui-même saisis (et dans les 24h)."""

    def has_object_permission(self, request, view, obj):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        dossier = obj if hasattr(obj, "agent_saisisseur") else getattr(obj, "dossier", None)
        if dossier is None:
            return True
        if request.user.role in (Role.ADMIN_SYSTEME, Role.ADMIN_REGIONAL):
            return True
        return dossier.agent_saisisseur_id == request.user.id and dossier.modifiable_librement
