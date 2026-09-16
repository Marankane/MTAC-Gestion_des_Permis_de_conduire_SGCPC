from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services


class TableauDeBordAPIView(APIView):
    """GET /api/v1/stats/tableau-de-bord/ — toutes les statistiques en un seul appel,
    pratique pour un futur dashboard mobile ou une intégration externe."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "resume": services.resume_general(),
                "par_mois": services.confiscations_par_mois(),
                "par_region": services.confiscations_par_region(),
                "par_type_incident": services.confiscations_par_type_incident(),
                "decisions": services.taux_decisions(),
                "delais": services.delais_moyens_traitement(),
                "presence_commissions": services.taux_presence_commissions(),
            }
        )


class AlertesAPIView(APIView):
    """GET /api/v1/stats/alertes/ — dossiers en retard et sessions surbookées."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = services.alertes()
        return Response(
            {
                "nb_dossiers_en_retard": data["nb_dossiers_en_retard"],
                "dossiers_en_retard": [
                    {"id": d.id, "numero": d.numero, "conducteur": str(d.conducteur), "date_saisie": d.date_saisie}
                    for d in data["dossiers_en_retard"]
                ],
                "nb_sessions_surbookees": data["nb_sessions_surbookees"],
                "sessions_surbookees": [
                    {"id": s.id, "date_session": s.date_session, "lieu": s.lieu, "capacite": s.capacite,
                     "nb_dossiers": s.nombre_dossiers_programmes}
                    for s in data["sessions_surbookees"]
                ],
            }
        )
