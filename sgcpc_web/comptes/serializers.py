from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Utilisateur


class UtilisateurSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = Utilisateur
        fields = [
            "id", "username", "first_name", "last_name", "role", "role_display",
            "region", "telephone", "matricule",
        ]
        read_only_fields = fields


class SGCPCTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Ajoute le profil utilisateur (rôle, région...) directement dans la réponse de connexion,
    pour que l'app Flutter n'ait pas besoin d'un second appel."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["nom_complet"] = user.get_full_name() or user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["utilisateur"] = UtilisateurSerializer(self.user).data
        return data
