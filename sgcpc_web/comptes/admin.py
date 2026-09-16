from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Utilisateur, OTPCode


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "role", "region", "is_active")
    list_filter = ("role", "region", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("Informations métier", {"fields": ("role", "region", "telephone", "matricule", "otp_verifie")}),
    )


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ("utilisateur", "code", "cree_le", "expire_le", "utilise")
    list_filter = ("utilise",)
