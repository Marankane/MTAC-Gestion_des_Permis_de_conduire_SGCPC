from django.contrib import admin

from .models import Conducteur, Vehicule, Dossier, PieceJointe, HistoriqueDossier


@admin.register(Conducteur)
class ConducteurAdmin(admin.ModelAdmin):
    list_display = ("nom", "prenom", "numero_permis", "mention_permis", "type_permis", "telephone")
    search_fields = ("nom", "prenom", "numero_permis", "mention_permis")


@admin.register(Vehicule)
class VehiculeAdmin(admin.ModelAdmin):
    list_display = ("marque", "modele", "plaque", "type_vehicule")
    search_fields = ("plaque",)


class PieceJointeInline(admin.TabularInline):
    model = PieceJointe
    extra = 0


class HistoriqueInline(admin.TabularInline):
    model = HistoriqueDossier
    extra = 0
    readonly_fields = ("utilisateur", "action", "date_action", "details")
    can_delete = False


@admin.register(Dossier)
class DossierAdmin(admin.ModelAdmin):
    list_display = ("numero", "conducteur", "type_incident", "statut", "date_incident", "ville", "en_retard")
    list_filter = ("statut", "type_incident", "ville")
    search_fields = (
        "numero", "conducteur__nom", "conducteur__numero_permis",
        "conducteur__mention_permis", "vehicule__plaque",
    )
    inlines = [PieceJointeInline, HistoriqueInline]
    readonly_fields = ("uuid", "numero", "date_saisie", "date_derniere_modif")
