"""Routes de l'API REST (v1) — consommée par le web (AJAX) et l'application mobile Flutter."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from comptes.api_views import ProfilView, SGCPCTokenObtainPairView
from commissions.api_views import AuditionViewSet, ConvocationViewSet, SessionCommissionViewSet
from decisions.api_views import DecisionViewSet
from dossiers.api_views import ConducteurViewSet, DossierViewSet, VehiculeViewSet, VerificationPermisAPIView
from reporting_stats.api_views import AlertesAPIView, TableauDeBordAPIView
from restitution.api_views import RestitutionViewSet

router = DefaultRouter()
router.register("dossiers", DossierViewSet, basename="api-dossier")
router.register("conducteurs", ConducteurViewSet, basename="api-conducteur")
router.register("vehicules", VehiculeViewSet, basename="api-vehicule")
router.register("commissions/sessions", SessionCommissionViewSet, basename="api-session")
router.register("commissions/convocations", ConvocationViewSet, basename="api-convocation")
router.register("commissions/auditions", AuditionViewSet, basename="api-audition")
router.register("decisions", DecisionViewSet, basename="api-decision")
router.register("restitutions", RestitutionViewSet, basename="api-restitution")

urlpatterns = [
    path("auth/token/", SGCPCTokenObtainPairView.as_view(), name="api-token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path("auth/profil/", ProfilView.as_view(), name="api-profil"),
    path("permis/verifier/", VerificationPermisAPIView.as_view(), name="api-verifier-permis"),
    path("stats/tableau-de-bord/", TableauDeBordAPIView.as_view(), name="api-stats-dashboard"),
    path("stats/alertes/", AlertesAPIView.as_view(), name="api-stats-alertes"),
    path("", include(router.urls)),
]
