from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from dossiers.models import StatutDossier, HistoriqueDossier
from .models import Restitution
from .serializers import RestitutionSerializer


class RestitutionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Restitution.objects.select_related("decision__audition__convocation__dossier__conducteur")
    serializer_class = RestitutionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        en_attente = self.request.query_params.get("en_attente")
        if en_attente == "true":
            qs = qs.filter(date_remise__isnull=True)
        elif en_attente == "false":
            qs = qs.filter(date_remise__isnull=False)
        return qs

    @action(detail=True, methods=["post"])
    def restituer(self, request, pk=None):
        restitution = self.get_object()
        if not request.data.get("piece_identite_verifiee"):
            return Response(
                {"piece_identite_verifiee": "La vérification de la pièce d'identité est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        restitution.piece_identite_verifiee = True
        restitution.date_remise = timezone.now()
        restitution.remis_par = request.user
        restitution.save()

        dossier = restitution.decision.audition.convocation.dossier
        dossier.statut = StatutDossier.CLOTURE
        dossier.save()
        HistoriqueDossier.objects.create(
            dossier=dossier, utilisateur=request.user, action="Permis restitué (API) — dossier clôturé"
        )
        return Response(RestitutionSerializer(restitution).data)
