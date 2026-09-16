from django.conf import settings
from django.db import models

from decisions.models import Decision


class Restitution(models.Model):
    decision = models.OneToOneField(Decision, on_delete=models.CASCADE, related_name="restitution")
    bon_restitution_pdf = models.FileField(upload_to="restitutions/", null=True, blank=True)
    date_remise = models.DateTimeField(null=True, blank=True)
    remis_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="restitutions_effectuees"
    )
    piece_identite_verifiee = models.BooleanField(default=False)
    rappel_envoye = models.BooleanField(
        default=False, help_text="Rappel automatique 7 jours avant l'échéance de suspension"
    )

    class Meta:
        verbose_name = "Restitution"
        verbose_name_plural = "Restitutions"

    def __str__(self):
        return f"Restitution {self.decision.audition.convocation.dossier.numero}"

    @property
    def effectuee(self):
        return self.date_remise is not None
