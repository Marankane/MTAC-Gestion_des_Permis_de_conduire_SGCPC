from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from commissions.models import Audition
from dossiers.models import StatutDossier, HistoriqueDossier
from .forms import DecisionForm
from .models import Decision, TypeDecision
from .utils import generer_arrete_decision


@login_required
def creer_decision(request, audition_pk):
    audition = get_object_or_404(Audition, pk=audition_pk)
    dossier = audition.convocation.dossier

    if hasattr(audition, "decision"):
        return redirect("decisions:detail", pk=audition.decision.pk)

    if request.method == "POST":
        form = DecisionForm(request.POST)
        if form.is_valid():
            decision = form.save(commit=False)
            decision.audition = audition
            decision.decide_par = request.user
            decision.save()

            arrete = generer_arrete_decision(decision)
            decision.arrete_pdf = arrete
            decision.notifie_sms = True  # simulation
            decision.notifie_email = True  # simulation
            if decision.type_decision == TypeDecision.RETRAIT_DEFINITIF:
                decision.transmis_tribunal = True
            decision.save()

            dossier.statut = StatutDossier.DECIDE
            dossier.save()
            HistoriqueDossier.objects.create(
                dossier=dossier,
                utilisateur=request.user,
                action=f"Décision rendue : {decision.get_type_decision_display()}",
                details=decision.motivation,
            )

            # Créer automatiquement l'enregistrement de restitution si relaxe ou suspension
            if decision.type_decision in (TypeDecision.RELAXE, TypeDecision.SUSPENSION):
                from restitution.models import Restitution

                Restitution.objects.get_or_create(decision=decision)

            messages.success(request, f"Décision enregistrée pour le dossier {dossier.numero}.")
            return redirect("decisions:detail", pk=decision.pk)
    else:
        form = DecisionForm()

    return render(request, "decisions/creer.html", {"form": form, "audition": audition, "dossier": dossier})


@login_required
def detail_decision(request, pk):
    decision = get_object_or_404(Decision, pk=pk)
    return render(request, "decisions/detail.html", {"decision": decision})


@login_required
def telecharger_arrete(request, pk):
    decision = get_object_or_404(Decision, pk=pk)
    if not decision.arrete_pdf:
        decision.arrete_pdf = generer_arrete_decision(decision)
        decision.save()
    response = HttpResponse(decision.arrete_pdf.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="arrete_{decision.audition.convocation.dossier.numero}.pdf"'
    return response
