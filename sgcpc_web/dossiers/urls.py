from django.urls import path

from . import views

app_name = "dossiers"

urlpatterns = [
    path("", views.DossierListView.as_view(), name="liste"),
    path("nouveau/", views.creer_dossier, name="creer"),
    path("<int:pk>/", views.DossierDetailView.as_view(), name="detail"),
    path("<int:pk>/bordereau/", views.telecharger_bordereau, name="bordereau"),
    path("verifier/<uuid:dossier_uuid>/", views.verifier_dossier_public, name="verifier_public"),
    # Module 2 - vérification
    path("verification/", views.tableau_verification, name="tableau_verification"),
    path("verification/<int:pk>/valider/", views.valider_dossier, name="valider"),
    path("verification/<int:pk>/complement/", views.demander_complement, name="demander_complement"),
    path("verification/<int:pk>/rejeter/", views.rejeter_dossier, name="rejeter"),
]
