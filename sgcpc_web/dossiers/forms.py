from django import forms

from .models import Dossier, Conducteur, Vehicule, PieceJointe


class ConducteurForm(forms.ModelForm):
    class Meta:
        model = Conducteur
        fields = [
            "nom", "prenom", "date_naissance", "lieu_naissance", "numero_permis", "mention_permis",
            "type_permis", "statut_permis", "date_delivrance", "date_expiration", "date_suspension",
            "telephone", "email", "adresse",
        ]
        widgets = {
            "date_naissance": forms.DateInput(attrs={"type": "date"}),
        }


class VehiculeForm(forms.ModelForm):
    class Meta:
        model = Vehicule
        fields = ["marque", "modele", "plaque", "type_vehicule"]


class DossierForm(forms.ModelForm):
    class Meta:
        model = Dossier
        fields = [
            "date_incident",
            "ville",
            "quartier",
            "latitude",
            "longitude",
            "type_incident",
            "vitesse_excessive",
            "alcool",
            "stupefiants",
            "feu_rouge",
            "autres_circonstances",
            "nombre_blesses",
            "nombre_deces",
            "gravite",
        ]
        widgets = {
            "date_incident": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "autres_circonstances": forms.Textarea(attrs={"rows": 3}),
        }


class PieceJointeForm(forms.ModelForm):
    class Meta:
        model = PieceJointe
        fields = ["type_piece", "fichier"]


PieceJointeFormSet = forms.modelformset_factory(PieceJointe, form=PieceJointeForm, extra=3, can_delete=True)
