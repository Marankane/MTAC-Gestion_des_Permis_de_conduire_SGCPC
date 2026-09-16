from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from dossiers.models import Dossier, StatutDossier, HistoriqueDossier
from .forms import SessionCommissionForm, AuditionForm
from .models import SessionCommission, Convocation, StatutConvocation, Audition
from .utils import generer_lettre_convocation


@login_required
def liste_sessions(request):
    sessions = SessionCommission.objects.all().order_by("-date_session")
    return render(request, "commissions/liste_sessions.html", {"sessions": sessions})


@login_required
def creer_session(request):
    if request.method == "POST":
        form = SessionCommissionForm(request.POST)
        if form.is_valid():
            session = form.save()
            messages.success(request, "Session de commission créée.")
            return redirect("commissions:detail_session", pk=session.pk)
    else:
        form = SessionCommissionForm()
    return render(request, "commissions/creer_session.html", {"form": form})


@login_required
def detail_session(request, pk):
    session = get_object_or_404(SessionCommission, pk=pk)
    dossiers_disponibles = Dossier.objects.filter(statut=StatutDossier.VERIFIE)
    convocations = session.convocations.select_related("dossier", "dossier__conducteur")
    return render(
        request,
        "commissions/detail_session.html",
        {"session": session, "dossiers_disponibles": dossiers_disponibles, "convocations": convocations},
    )


@login_required
def programmer_dossier(request, session_pk, dossier_pk):
    """Convoque un dossier vérifié devant une session de commission (Module 3)."""
    session = get_object_or_404(SessionCommission, pk=session_pk)
    dossier = get_object_or_404(Dossier, pk=dossier_pk, statut=StatutDossier.VERIFIE)

    convocation = Convocation.objects.create(dossier=dossier, session=session)
    lettre = generer_lettre_convocation(convocation)
    convocation.lettre_pdf = lettre
    convocation.envoye_sms = True  # simulation
    convocation.envoye_email = True  # simulation
    convocation.save()

    dossier.statut = StatutDossier.PROGRAMME
    dossier.save()

    HistoriqueDossier.objects.create(
        dossier=dossier,
        utilisateur=request.user,
        action="Programmé en commission",
        details=f"Session du {session.date_session:%d/%m/%Y %H:%M} - {session.lieu}",
    )
    messages.success(request, f"Dossier {dossier.numero} convoqué (lettre + SMS + email envoyés).")
    return redirect("commissions:detail_session", pk=session.pk)


@login_required
def telecharger_convocation(request, pk):
    convocation = get_object_or_404(Convocation, pk=pk)
    if not convocation.lettre_pdf:
        convocation.lettre_pdf = generer_lettre_convocation(convocation)
        convocation.save()
    response = HttpResponse(convocation.lettre_pdf.read(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="convocation_{convocation.dossier.numero}.pdf"'
    return response


@login_required
def marquer_presence(request, pk, statut):
    convocation = get_object_or_404(Convocation, pk=pk)
    mapping = {"present": StatutConvocation.PRESENT, "absent": StatutConvocation.ABSENT}
    if statut in mapping:
        convocation.statut = mapping[statut]
        convocation.save()
        messages.info(request, f"{convocation.dossier.numero} marqué {statut}.")
    return redirect("commissions:detail_session", pk=convocation.session.pk)


@login_required
def enregistrer_audition(request, convocation_pk):
    """Module 4 : audition du conducteur devant la commission."""
    convocation = get_object_or_404(Convocation, pk=convocation_pk)

    if hasattr(convocation, "audition"):
        return redirect("decisions:creer", audition_pk=convocation.audition.pk)

    if request.method == "POST":
        form = AuditionForm(request.POST, request.FILES)
        if form.is_valid():
            audition = form.save(commit=False)
            audition.convocation = convocation
            audition.enregistre_par = request.user
            audition.save()
            messages.success(request, "Audition enregistrée. Vous pouvez maintenant saisir la décision.")
            return redirect("decisions:creer", audition_pk=audition.pk)
    else:
        form = AuditionForm()

    return render(request, "commissions/enregistrer_audition.html", {"form": form, "convocation": convocation})
