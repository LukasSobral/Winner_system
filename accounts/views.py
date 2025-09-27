# accounts/views.py
from rest_framework import viewsets, permissions, status , filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from .models import User
from .serializers import UserSerializer, UserCreateSerializer, ChangePasswordSerializer
from .permissions import IsCoordinator
from django_filters.rest_framework import DjangoFilterBackend


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD de usuários.
    - Coordenadores podem criar, editar e deletar
    - Outros papéis só podem visualizar
    """
    queryset = User.objects.all().order_by("id")

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id", "username", "email", "role"]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["id", "username", "email", "first_name", "last_name", "role"]
    ordering = ["id"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [permissions.IsAuthenticated(), IsCoordinator()]
        return [permissions.IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        """Criação com resposta amigável"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"success": f"Usuário {user.username} criado com sucesso!", "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        """Exclusão com resposta amigável"""
        user = self.get_object()
        username = user.username
        self.perform_destroy(user)
        return Response({"success": f"Usuário {username} removido com sucesso."}, status=status.HTTP_200_OK)



class MeViewSet(viewsets.ViewSet):
    """
    Endpoints relacionados ao usuário logado:
    - GET /api/accounts/me/ → retorna dados do usuário
    - PATCH /api/accounts/me/change-password/ → altera senha
    """
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="")
    def retrieve_me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["patch"], url_path="change-password")
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_password = serializer.validated_data["old_password"]
        new_password = serializer.validated_data["new_password"]

        if not check_password(old_password, request.user.password):
            return Response({"error": "Senha antiga incorreta"}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(new_password)
        request.user.save()
        return Response({"success": "Senha alterada com sucesso"})
