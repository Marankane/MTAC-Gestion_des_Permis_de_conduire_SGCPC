from django.contrib import admin

from .models import Decision


@admin.register(Decision)
class DecisionAdmin(admin.ModelAdmin):
    list_display = ("audition", "type_decision", "date_decision", "decide_par", "transmis_tribunal")
    list_filter = ("type_decision", "transmis_tribunal")
