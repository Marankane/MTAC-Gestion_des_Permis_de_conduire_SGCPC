from django import forms

from .models import Decision


class DecisionForm(forms.ModelForm):
    class Meta:
        model = Decision
        fields = ["type_decision", "duree_suspension_mois", "motivation"]
        widgets = {
            "motivation": forms.Textarea(attrs={"rows": 5}),
        }

    def clean(self):
        cleaned = super().clean()
        type_decision = cleaned.get("type_decision")
        duree = cleaned.get("duree_suspension_mois")
        if type_decision == "SUSPENSION" and not duree:
            raise forms.ValidationError("La durée de suspension (en mois) est obligatoire pour une suspension temporaire.")
        if type_decision == "SUSPENSION" and duree and not (1 <= duree <= 36):
            raise forms.ValidationError("La durée de suspension doit être comprise entre 1 et 36 mois.")
        if not cleaned.get("motivation"):
            raise forms.ValidationError("La décision doit être motivée.")
        return cleaned
