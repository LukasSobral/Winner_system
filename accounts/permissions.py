from rest_framework import permissions


class IsCoordinator(permissions.BasePermission):
    """
    Permite acesso apenas para COORDINATOR.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "COORDINATOR"


class IsCoordinatorOrReadOnly(permissions.BasePermission):
    """
    Coordenador pode tudo.
    Outros papéis só podem leitura (GET, HEAD, OPTIONS).
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.method in permissions.SAFE_METHODS:
            return True

        return request.user.role == "COORDINATOR"


class IsTeacherOrCoordinator(permissions.BasePermission):
    """
    Coordenadores podem tudo.
    Professores podem acessar apenas as próprias aulas/sessões.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["TEACHER", "COORDINATOR"]

    def has_object_permission(self, request, view, obj):
        if request.user.role == "COORDINATOR":
            return True
        if request.user.role == "TEACHER":
            if hasattr(obj, "teacher"):
                return obj.teacher == request.user
            if hasattr(obj, "classroom") and hasattr(obj.classroom, "teacher"):
                return obj.classroom.teacher == request.user

        return False


class IsStudentItself(permissions.BasePermission):
    """
    Alunos só podem acessar os próprios dados.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "STUDENT"

    def has_object_permission(self, request, view, obj):
        return obj.id == request.user.id
