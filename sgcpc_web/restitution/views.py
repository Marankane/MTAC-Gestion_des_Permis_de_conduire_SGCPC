from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from dossiers.models import StatutDossier, HistoriqueDossier
from .models import Restitution


@login_required
def liste_restitutions(request):
    en_attente = Restitution.objects.filter(date_remise__isnull=True).select_related(
        "decision__audition__convocation__dossier__conducteur"
    )
    cloturees = Restitution.objects.filter(date_remise__isnull=False).select_related(
        "decision__audition__convocation__dossier__conducteur"
    )
    return render(
        request, "restitution/liste.html", {"en_attente": en_attente, "cloturees": cloturees}
    )


@login_required
def restituer(request, pk):
    restitution = get_object_or_404(Restitution, pk=pk)
    dossier = restitution.decision.audition.convocation.dossier

    if request.method == "POST":
        if not request.POST.get("piece_identite"):
            messages.error(request, "La vérification de la pièce d'identité est obligatoire avant restitution.")
            return redirect("restitution:liste")

        restitution.piece_identite_verifiee = True
        restitution.date_remise = timezone.now()
        restitution.remis_par = request.user
        restitution.save()

        dossier.statut = StatutDossier.CLOTURE
        dossier.save()
        HistoriqueDossier.objects.create(
            dossier=dossier,
            utilisateur=request.user,
            action="Permis restitué — dossier clôturé et archivé",
        )
        messages.success(request, f"Permis restitué pour le dossier {dossier.numero}. Dossier clôturé.")
    return redirect("restitution:liste")
