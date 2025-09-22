from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from .models import User
from .serializers import UserSerializer


class MeView(generics.RetrieveUpdateAPIView):
    """Retorna e atualiza o usuário logado"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.UpdateAPIView):
    """Permite o usuário alterar a própria senha"""
    serializer_class = UserSerializer  # não vamos expor a senha aqui
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")

        if not old_password or not new_password:
            return Response(
                {"error": "É necessário informar old_password e new_password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not check_password(old_password, user.password):
            return Response(
                {"error": "Senha antiga incorreta"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()

        return Response(
            {"success": "Senha alterada com sucesso"},
            status=status.HTTP_200_OK,
        )
