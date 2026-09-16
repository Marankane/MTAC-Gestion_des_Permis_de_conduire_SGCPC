from django.http import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from comptes.permissions import EstMembreCommission
from dossiers.models import Dossier, StatutDossier, HistoriqueDossier
from .models import SessionCommission, Convocation, Audition, StatutConvocation
from .serializers import SessionCommissionSerializer, ConvocationSerializer, AuditionSerializer
from .utils import generer_lettre_convocation


class SessionCommissionViewSet(viewsets.ModelViewSet):
    queryset = SessionCommission.objects.all().order_by("-date_session")
    serializer_class = SessionCommissionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), EstMembreCommission()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], url_path="programmer/(?P<dossier_id>[^/.]+)")
    def programmer_dossier(self, request, pk=None, dossier_id=None):
        session = self.get_object()
        dossier = Dossier.objects.get(pk=dossier_id, statut=StatutDossier.VERIFIE)

        convocation = Convocation.objects.create(dossier=dossier, session=session)
        convocation.lettre_pdf = generer_lettre_convocation(convocation)
        convocation.envoye_sms = True
        convocation.envoye_email = True
        convocation.save()

        dossier.statut = StatutDossier.PROGRAMME
        dossier.save()
        HistoriqueDossier.objects.create(
            dossier=dossier, utilisateur=request.user, action="Programmé en commission (API)"
        )
        return Response(ConvocationSerializer(convocation).data, status=status.HTTP_201_CREATED)


class ConvocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Convocation.objects.select_related("dossier", "dossier__conducteur", "session")
    serializer_class = ConvocationSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["get"])
    def lettre_pdf(self, request, pk=None):
        convocation = self.get_object()
        if not convocation.lettre_pdf:
            convocation.lettre_pdf = generer_lettre_convocation(convocation)
            convocation.save()
        response = HttpResponse(convocation.lettre_pdf.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="convocation_{convocation.dossier.numero}.pdf"'
        return response

    @action(detail=True, methods=["post"])
    def presence(self, request, pk=None):
        """Body: {"statut": "present" | "absent"}"""
        convocation = self.get_object()
        mapping = {"present": StatutConvocation.PRESENT, "absent": StatutConvocation.ABSENT}
        statut = request.data.get("statut")
        if statut not in mapping:
            return Response({"statut": "Doit être 'present' ou 'absent'."}, status=status.HTTP_400_BAD_REQUEST)
        convocation.statut = mapping[statut]
        convocation.save()
        return Response(ConvocationSerializer(convocation).data)


class AuditionViewSet(viewsets.ModelViewSet):
    queryset = Audition.objects.select_related("convocation__dossier")
    serializer_class = AuditionSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated(), EstMembreCommission()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(enregistre_par=self.request.user)
