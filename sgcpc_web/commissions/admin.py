from django.contrib import admin

from .models import SessionCommission, Convocation, Audition


@admin.register(SessionCommission)
class SessionCommissionAdmin(admin.ModelAdmin):
    list_display = ("date_session", "lieu", "capacite", "president", "nombre_dossiers_programmes", "surbookee")
    filter_horizontal = ("membres",)


@admin.register(Convocation)
class ConvocationAdmin(admin.ModelAdmin):
    list_display = ("dossier", "session", "statut", "date_envoi", "delai_respecte")
    list_filter = ("statut",)


@admin.register(Audition)
class AuditionAdmin(admin.ModelAdmin):
    list_display = ("convocation", "date_audition", "enregistre_par")
