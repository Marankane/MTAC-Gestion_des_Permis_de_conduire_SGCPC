from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.TextChoices):
    AGENT_POLICE = "AGENT_POLICE", "Agent de Police"
    GENDARME = "GENDARME", "Gendarme"
    ADMIN_REGIONAL = "ADMIN_REGIONAL", "Administrateur régional"
    SECRETAIRE_COMMISSION = "SECRETAIRE_COMMISSION", "Secrétaire de commission"
    MEMBRE_COMMISSION = "MEMBRE_COMMISSION", "Membre de commission"
    ADMIN_SYSTEME = "ADMIN_SYSTEME", "Administrateur système"


class Utilisateur(AbstractUser):
    """Utilisateur du système avec rôle métier (RBAC) et rattachement régional."""

    role = models.CharField(max_length=32, choices=Role.choices)
    region = models.CharField(max_length=100, blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    matricule = models.CharField(max_length=50, blank=True, help_text="Matricule professionnel (Police/Gendarmerie)")
    otp_verifie = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    def is_force_ordre(self):
        return self.role in (Role.AGENT_POLICE, Role.GENDARME)

    def is_commission(self):
        return self.role in (Role.SECRETAIRE_COMMISSION, Role.MEMBRE_COMMISSION)


class OTPCode(models.Model):
    """Code OTP envoyé par SMS pour l'authentification renforcée."""

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name="otp_codes")
    code = models.CharField(max_length=6)
    cree_le = models.DateTimeField(auto_now_add=True)
    expire_le = models.DateTimeField()
    utilise = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Code OTP"
        verbose_name_plural = "Codes OTP"

    def __str__(self):
        return f"OTP {self.code} - {self.utilisateur}"
