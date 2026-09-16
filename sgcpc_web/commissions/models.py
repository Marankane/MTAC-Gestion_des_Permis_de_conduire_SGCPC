from django.conf import settings
from django.db import models

from dossiers.models import Dossier


class SessionCommission(models.Model):
    date_session = models.DateTimeField()
    lieu = models.CharField(max_length=255)
    capacite = models.PositiveIntegerField(default=10, help_text="Nombre de dossiers max pour cette session")
    president = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sessions_presidees"
    )
    membres = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="sessions_membre", blank=True)

    class Meta:
        verbose_name = "Session de commission"
        verbose_name_plural = "Sessions de commission"
        ordering = ["-date_session"]

    def __str__(self):
        return f"Commission du {self.date_session:%d/%m/%Y %H:%M} - {self.lieu}"

    @property
    def nombre_dossiers_programmes(self):
        return self.convocations.count()

    @property
    def surbookee(self):
        return self.nombre_dossiers_programmes > self.capacite


class StatutConvocation(models.TextChoices):
    ENVOYEE = "ENVOYEE", "Envoyée"
    PRESENT = "PRESENT", "Présent"
    ABSENT = "ABSENT", "Absent"
    REPORTEE = "REPORTEE", "Reportée"


class Convocation(models.Model):
    dossier = models.OneToOneField(Dossier, on_delete=models.CASCADE, related_name="convocation")
    session = models.ForeignKey(SessionCommission, on_delete=models.CASCADE, related_name="convocations")
    date_envoi = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=15, choices=StatutConvocation.choices, default=StatutConvocation.ENVOYEE)
    lettre_pdf = models.FileField(upload_to="convocations/", null=True, blank=True)
    envoye_sms = models.BooleanField(default=False)
    envoye_email = models.BooleanField(default=False)
    envoye_courrier = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Convocation"
        verbose_name_plural = "Convocations"

    def __str__(self):
        return f"Convocation {self.dossier.numero} - {self.session}"

    @property
    def delai_respecte(self):
        """Un conducteur doit être convoqué au moins 7 jours avant la session."""
        return (self.session.date_session - self.date_envoi).days >= 7


class Audition(models.Model):
    convocation = models.OneToOneField(Convocation, on_delete=models.CASCADE, related_name="audition")
    explications_conducteur = models.TextField(blank=True)
    pieces_supplementaires = models.FileField(upload_to="auditions/", null=True, blank=True)
    date_audition = models.DateTimeField(auto_now_add=True)
    enregistre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Audition"
        verbose_name_plural = "Auditions"

    def __str__(self):
        return f"Audition {self.convocation.dossier.numero}"
