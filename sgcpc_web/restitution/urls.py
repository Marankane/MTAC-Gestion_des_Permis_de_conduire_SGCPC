from django.urls import path

from . import views

app_name = "restitution"

urlpatterns = [
    path("", views.liste_restitutions, name="liste"),
    path("<int:pk>/restituer/", views.restituer, name="restituer"),
]
