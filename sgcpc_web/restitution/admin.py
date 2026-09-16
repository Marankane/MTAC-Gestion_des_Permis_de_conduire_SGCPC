from django.contrib import admin

from .models import Restitution


@admin.register(Restitution)
class RestitutionAdmin(admin.ModelAdmin):
    list_display = ("decision", "date_remise", "effectuee", "piece_identite_verifiee", "rappel_envoye")
    list_filter = ("piece_identite_verifiee", "rappel_envoye")
