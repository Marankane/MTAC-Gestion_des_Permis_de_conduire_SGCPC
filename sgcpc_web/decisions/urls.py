from django.urls import path

from . import views

app_name = "decisions"

urlpatterns = [
    path("nouvelle/<int:audition_pk>/", views.creer_decision, name="creer"),
    path("<int:pk>/", views.detail_decision, name="detail"),
    path("<int:pk>/arrete/", views.telecharger_arrete, name="arrete_pdf"),
]
