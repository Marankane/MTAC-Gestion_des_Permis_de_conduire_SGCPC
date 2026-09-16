from django.conf import settings
from django.db import models

from commissions.models import Audition


class TypeDecision(models.TextChoices):
    RELAXE = "RELAXE", "Relaxe (restitution immédiate)"
    SUSPENSION = "SUSPENSION", "Suspension temporaire"
    RETRAIT_DEFINITIF = "RETRAIT_DEFINITIF", "Retrait définitif"
    FORMATION_OBLIGATOIRE = "FORMATION_OBLIGATOIRE", "Obligation de formation"


class Decision(models.Model):
    audition = models.OneToOneField(Audition, on_delete=models.CASCADE, related_name="decision")
    type_decision = models.CharField(max_length=25, choices=TypeDecision.choices)
    duree_suspension_mois = models.PositiveIntegerField(
        null=True, blank=True, help_text="Durée en mois (1 à 36) si suspension temporaire"
    )
    motivation = models.TextField(help_text="La décision doit être motivée (obligatoire)")
    arrete_pdf = models.FileField(upload_to="decisions/", null=True, blank=True)

    date_decision = models.DateTimeField(auto_now_add=True)
    decide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    notifie_sms = models.BooleanField(default=False)
    notifie_email = models.BooleanField(default=False)
    notifie_courrier = models.BooleanField(default=False)

    transmis_tribunal = models.BooleanField(default=False, help_text="Si retrait définitif")

    class Meta:
        verbose_name = "Décision"
        verbose_name_plural = "Décisions"

    def __str__(self):
        return f"{self.get_type_decision_display()} - {self.audition.convocation.dossier.numero}"

    @property
    def date_fin_suspension(self):
        if self.type_decision == TypeDecision.SUSPENSION and self.duree_suspension_mois:
            from dateutil.relativedelta import relativedelta

            return self.date_decision + relativedelta(months=self.duree_suspension_mois)
        return None

    @property
    def delai_recours_expire(self):
        """Le conducteur dispose de 15 jours de recours."""
        from django.utils import timezone
        from datetime import timedelta

        return timezone.now() > self.date_decision + timedelta(days=15)
