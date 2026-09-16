from django.http import HttpResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from comptes.permissions import EstAdminRegionalOuSysteme, EstForceDeLOrdre, LectureSeuleOuAuteur
from .models import Conducteur, Vehicule, Dossier, PieceJointe, HistoriqueDossier, StatutDossier
from .serializers import (
    ConducteurSerializer,
    VehiculeSerializer,
    DossierListSerializer,
    DossierDetailSerializer,
    DossierCreateSerializer,
    PieceJointeSerializer,
    VerificationActionSerializer,
)
from .utils import generer_bordereau_pdf


class ConducteurViewSet(viewsets.ReadOnlyModelViewSet):
    """Recherche d'un conducteur par n° de permis (vérification croisée, module 1/2)."""

    queryset = Conducteur.objects.all()
    serializer_class = ConducteurSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["numero_permis", "mention_permis", "nom", "prenom"]


class VerificationPermisAPIView(APIView):
    """Vérification publique d'un permis par numéro et mention."""

    permission_classes = [AllowAny]

    def get(self, request):
        numero = request.query_params.get("numero_permis", "").strip()
        mention = request.query_params.get("mention_permis", "").strip()
        if not numero or not mention:
            return Response(
                {"detail": "Le numéro et la mention du permis sont obligatoires."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            conducteur = Conducteur.objects.get(numero_permis=numero, mention_permis=mention)
        except Conducteur.DoesNotExist:
            return Response({"detail": "Aucun permis trouvé."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ConducteurSerializer(conducteur).data)


class VehiculeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Vehicule.objects.all()
    serializer_class = VehiculeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ["plaque"]


class DossierViewSet(viewsets.ModelViewSet):
    """
    Endpoint central du Module 1/2 pour le web et l'app mobile Flutter.

    - POST   /api/v1/dossiers/                 -> saisie terrain (Police/Gendarmerie)
    - GET    /api/v1/dossiers/                 -> liste (filtrée par rôle)
    - GET    /api/v1/dossiers/{id}/            -> détail complet
    - POST   /api/v1/dossiers/{id}/valider/    -> Module 2 : validation admin
    - POST   /api/v1/dossiers/{id}/rejeter/    -> Module 2 : rejet (motif obligatoire)
    - POST   /api/v1/dossiers/{id}/complement/ -> Module 2 : demande de complément
    - GET    /api/v1/dossiers/{id}/bordereau/  -> téléchargement du bordereau PDF
    - POST   /api/v1/dossiers/{id}/pieces/     -> upload d'une pièce jointe (photo, PV...)
    """

    queryset = Dossier.objects.select_related("conducteur", "vehicule", "agent_saisisseur").prefetch_related(
        "pieces", "historique"
    )
    permission_classes = [IsAuthenticated, LectureSeuleOuAuteur]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["statut", "type_incident", "ville"]
    search_fields = ["numero", "conducteur__nom", "conducteur__numero_permis", "vehicule__plaque"]
    ordering_fields = ["date_incident", "date_saisie"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_force_ordre():
            qs = qs.filter(agent_saisisseur=user)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return DossierCreateSerializer
        if self.action == "list":
            return DossierListSerializer
        return DossierDetailSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsAuthenticated(), EstForceDeLOrdre()]
        if self.action in ("valider", "rejeter", "demander_complement"):
            return [IsAuthenticated(), EstAdminRegionalOuSysteme()]
        return super().get_permissions()

    @action(detail=True, methods=["get"])
    def bordereau(self, request, pk=None):
        dossier = self.get_object()
        pdf_file = generer_bordereau_pdf(dossier)
        response = HttpResponse(pdf_file.read(), content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="bordereau_{dossier.numero}.pdf"'
        return response

    @action(detail=True, methods=["post"])
    def valider(self, request, pk=None):
        dossier = self.get_object()
        dossier.statut = StatutDossier.VERIFIE
        dossier.verificateur = request.user
        dossier.date_verification = timezone.now()
        dossier.save()
        HistoriqueDossier.objects.create(
            dossier=dossier, utilisateur=request.user, action="Dossier validé (API) et transmis à la commission"
        )
        return Response(DossierDetailSerializer(dossier).data)

    @action(detail=True, methods=["post"])
    def rejeter(self, request, pk=None):
        serializer = VerificationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        motif = serializer.validated_data.get("motif", "")
        if not motif:
            return Response({"motif": "Le motif de rejet est obligatoire."}, status=status.HTTP_400_BAD_REQUEST)

        dossier = self.get_object()
        dossier.statut = StatutDossier.REJETE
        dossier.motif_rejet = motif
        dossier.verificateur = request.user
        dossier.date_verification = timezone.now()
        dossier.save()
        HistoriqueDossier.objects.create(
            dossier=dossier, utilisateur=request.user, action="Dossier rejeté (API)", details=motif
        )
        return Response(DossierDetailSerializer(dossier).data)

    @action(detail=True, methods=["post"], url_path="complement")
    def demander_complement(self, request, pk=None):
        serializer = VerificationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        motif = serializer.validated_data.get("motif", "")

        dossier = self.get_object()
        dossier.statut = StatutDossier.COMPLEMENT_DEMANDE
        dossier.motif_rejet = motif
        dossier.save()
        HistoriqueDossier.objects.create(
            dossier=dossier, utilisateur=request.user, action="Complément demandé (API)", details=motif
        )
        return Response(DossierDetailSerializer(dossier).data)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser], url_path="pieces")
    def ajouter_piece(self, request, pk=None):
        """Upload d'une pièce jointe (photo du permis, carte grise, PV, etc.) — utilisé par
        l'app mobile pour envoyer les photos prises sur le terrain, y compris après une
        saisie hors-ligne."""
        dossier = self.get_object()
        serializer = PieceJointeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(dossier=dossier)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
