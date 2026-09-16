from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from comptes.permissions import EstMembreCommission
from dossiers.models import StatutDossier, HistoriqueDossier
from restitution.models import Restitution
from .models import Decision, TypeDecision
from .serializers import DecisionSerializer
from .utils import generer_arrete_decision


class DecisionViewSet(viewsets.ModelViewSet):
    queryset = Decision.objects.select_related("audition__convocation__dossier")
    serializer_class = DecisionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), EstMembreCommission()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        decision = serializer.save(decide_par=self.request.user)
        decision.arrete_pdf = generer_arrete_decision(decision)
        decision.notifie_sms = True
        decision.notifie_email = True
        if decision.type_decision == TypeDecision.RETRAIT_DEFINITIF:
            decision.transmis_tribunal = True
        decision.save()

        dossier = decision.audition.convocation.dossier
        dossier.statut = StatutDossier.DECIDE
        dossier.save()
        HistoriqueDossier.objects.create(
            dossier=dossier,
            utilisateur=self.request.user,
            action=f"Décision rendue (API) : {decision.get_type_decision_display()}",
            details=decision.motivation,
        )
        if decision.type_decision in (TypeDecision.RELAXE, TypeDecision.SUSPENSION):
            Restitution.objects.get_or_create(decision=decision)

    @action(detail=True, methods=["get"])
    def arrete_pdf(self, request, pk=None):
        decision = self.get_object()
        if not decision.arrete_pdf:
            decision.arrete_pdf = generer_arrete_decision(decision)
            decision.save()
        response = HttpResponse(decision.arrete_pdf.read(), content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="arrete_{decision.audition.convocation.dossier.numero}.pdf"'
        )
        return response
