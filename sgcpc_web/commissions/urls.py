from django.urls import path

from . import views

app_name = "commissions"

urlpatterns = [
    path("", views.liste_sessions, name="liste"),
    path("nouvelle/", views.creer_session, name="creer"),
    path("<int:pk>/", views.detail_session, name="detail_session"),
    path("<int:session_pk>/programmer/<int:dossier_pk>/", views.programmer_dossier, name="programmer"),
    path("convocation/<int:pk>/pdf/", views.telecharger_convocation, name="convocation_pdf"),
    path("convocation/<int:pk>/presence/<str:statut>/", views.marquer_presence, name="marquer_presence"),
    path("audition/<int:convocation_pk>/", views.enregistrer_audition, name="audition"),
]
