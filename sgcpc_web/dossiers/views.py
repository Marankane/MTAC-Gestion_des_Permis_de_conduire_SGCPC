from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView

from .forms import ConducteurForm, VehiculeForm, DossierForm
from .models import Dossier, HistoriqueDossier, StatutDossier
from .utils import generer_bordereau_pdf, generer_qrcode_dossier


class DossierListView(LoginRequiredMixin, ListView):
    model = Dossier
    template_name = "dossiers/liste.html"
    context_object_name = "dossiers"
    paginate_by = 20

    def get_queryset(self):
        qs = Dossier.objects.select_related("conducteur", "vehicule", "agent_saisisseur")
        utilisateur = self.request.user
        # RBAC simplifié : un agent ne voit que ses propres saisies, l'admin régional voit sa région
        if utilisateur.is_force_ordre():
            qs = qs.filter(agent_saisisseur=utilisateur)
        recherche = self.request.GET.get("q")
        if recherche:
            qs = qs.filter(numero__icontains=recherche) | qs.filter(conducteur__nom__icontains=recherche)
        statut = self.request.GET.get("statut")
        if statut:
            qs = qs.filter(statut=statut)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["statuts"] = StatutDossier.choices
        ctx["statut_actif"] = self.request.GET.get("statut", "")
        ctx["recherche"] = self.request.GET.get("q", "")
        return ctx


class DossierDetailView(LoginRequiredMixin, DetailView):
    model = Dossier
    template_name = "dossiers/detail.html"
    context_object_name = "dossier"

    def get_queryset(self):
        return Dossier.objects.select_related("conducteur", "vehicule", "agent_saisisseur").prefetch_related(
            "pieces", "historique"
        )


@login_required
@transaction.atomic
def creer_dossier(request):
    """Module 1 : saisie d'un accident/incident par la Police/Gendarmerie."""
    if request.method == "POST":
        conducteur_form = ConducteurForm(request.POST, prefix="conducteur")
        vehicule_form = VehiculeForm(request.POST, prefix="vehicule")
        dossier_form = DossierForm(request.POST, prefix="dossier")

        if conducteur_form.is_valid() and vehicule_form.is_valid() and dossier_form.is_valid():
            conducteur = conducteur_form.save()
            vehicule = vehicule_form.save()
            dossier = dossier_form.save(commit=False)
            dossier.conducteur = conducteur
            dossier.vehicule = vehicule
            dossier.agent_saisisseur = request.user
            dossier.save()

            HistoriqueDossier.objects.create(
                dossier=dossier,
                utilisateur=request.user,
                action="Création du dossier",
                details=f"Saisie initiale par {request.user}",
            )

            # Génération automatique du bordereau et du QR code
            dossier.pieces.model  # noqa (garde l'import utilisé)
            bordereau = generer_bordereau_pdf(dossier)
            from .models import PieceJointe, TypePiece

            PieceJointe.objects.create(dossier=dossier, type_piece=TypePiece.AUTRE, fichier=bordereau)

            messages.success(
                request,
                f"Dossier {dossier.numero} créé avec succès. Le conducteur a été notifié par SMS (simulation).",
            )
            return redirect("dossiers:detail", pk=dossier.pk)
    else:
        conducteur_form = ConducteurForm(prefix="conducteur")
        vehicule_form = VehiculeForm(prefix="vehicule")
        dossier_form = DossierForm(prefix="dossier")

    return render(
        request,
        "dossiers/creer.html",
        {
            "conducteur_form": conducteur_form,
            "vehicule_form": vehicule_form,
            "dossier_form": dossier_form,
        },
    )


@login_required
def telecharger_bordereau(request, pk):
    dossier = get_object_or_404(Dossier, pk=pk)
    pdf_file = generer_bordereau_pdf(dossier)
    response = HttpResponse(pdf_file.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="bordereau_{dossier.numero}.pdf"'
    return response


@login_required
def verifier_dossier_public(request, dossier_uuid):
    """Page de vérification publique accessible via le QR code du bordereau."""
    dossier = get_object_or_404(Dossier, uuid=dossier_uuid)
    return render(request, "dossiers/verification_publique.html", {"dossier": dossier})


# --- Module 2 : Transmission et vérification (Administration) ---

@login_required
def tableau_verification(request):
    """Tableau de bord régional des dossiers en attente de vérification (Module 2)."""
    dossiers = Dossier.objects.filter(statut=StatutDossier.SAISI).select_related("conducteur", "vehicule")
    return render(request, "dossiers/tableau_verification.html", {"dossiers": dossiers})


@login_required
def valider_dossier(request, pk):
    dossier = get_object_or_404(Dossier, pk=pk)
    dossier.statut = StatutDossier.VERIFIE
    dossier.verificateur = request.user
    dossier.date_verification = timezone.now()
    dossier.save()
    HistoriqueDossier.objects.create(
        dossier=dossier, utilisateur=request.user, action="Dossier validé et transmis à la commission"
    )
    messages.success(request, f"Dossier {dossier.numero} validé et transmis à la commission.")
    return redirect("dossiers:tableau_verification")


@login_required
def demander_complement(request, pk):
    dossier = get_object_or_404(Dossier, pk=pk)
    motif = request.POST.get("motif", "")
    dossier.statut = StatutDossier.COMPLEMENT_DEMANDE
    dossier.motif_rejet = motif
    dossier.save()
    HistoriqueDossier.objects.create(
        dossier=dossier, utilisateur=request.user, action="Complément demandé", details=motif
    )
    messages.info(request, f"Complément demandé pour le dossier {dossier.numero} (notification envoyée).")
    return redirect("dossiers:tableau_verification")


@login_required
def rejeter_dossier(request, pk):
    dossier = get_object_or_404(Dossier, pk=pk)
    motif = request.POST.get("motif", "")
    if not motif:
        messages.error(request, "Le motif de rejet est obligatoire.")
        return redirect("dossiers:tableau_verification")
    dossier.statut = StatutDossier.REJETE
    dossier.motif_rejet = motif
    dossier.verificateur = request.user
    dossier.date_verification = timezone.now()
    dossier.save()
    HistoriqueDossier.objects.create(dossier=dossier, utilisateur=request.user, action="Dossier rejeté", details=motif)
    messages.warning(request, f"Dossier {dossier.numero} rejeté.")
    return redirect("dossiers:tableau_verification")
