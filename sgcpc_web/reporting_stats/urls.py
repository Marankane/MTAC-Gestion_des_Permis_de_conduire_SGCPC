from django.urls import path

from . import views

app_name = "reporting_stats"

urlpatterns = [
    path("", views.tableau_de_bord, name="dashboard"),
    path("export/csv/", views.export_csv, name="export_csv"),
    path("export/pdf/", views.export_pdf, name="export_pdf"),
    path("alertes/", views.alertes_view, name="alertes"),
]
