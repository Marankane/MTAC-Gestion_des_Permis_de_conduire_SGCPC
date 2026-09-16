from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from .serializers import SGCPCTokenObtainPairSerializer, UtilisateurSerializer


class SGCPCTokenObtainPairView(TokenObtainPairView):
    serializer_class = SGCPCTokenObtainPairSerializer


class ProfilView(RetrieveAPIView):
    """GET /api/v1/auth/profil/ — infos de l'utilisateur connecté (pratique pour l'app mobile)."""

    serializer_class = UtilisateurSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
