from django import forms

from comptes.models import Utilisateur
from .models import SessionCommission, Audition


class SessionCommissionForm(forms.ModelForm):
    class Meta:
        model = SessionCommission
        fields = ["date_session", "lieu", "capacite", "president", "membres"]
        widgets = {
            "date_session": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "membres": forms.SelectMultiple(attrs={"size": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["president"].queryset = Utilisateur.objects.filter(
            role__in=["MEMBRE_COMMISSION", "SECRETAIRE_COMMISSION", "ADMIN_SYSTEME"]
        )
        self.fields["membres"].queryset = Utilisateur.objects.filter(
            role__in=["MEMBRE_COMMISSION", "SECRETAIRE_COMMISSION"]
        )


class AuditionForm(forms.ModelForm):
    class Meta:
        model = Audition
        fields = ["explications_conducteur", "pieces_supplementaires"]
        widgets = {
            "explications_conducteur": forms.Textarea(attrs={"rows": 5}),
        }
