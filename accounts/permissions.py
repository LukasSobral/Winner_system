from rest_framework import permissions


class IsCoordinator(permissions.BasePermission):
    """
    Permite acesso apenas para COORDINATOR.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "COORDINATOR"


class IsTeacherOrCoordinator(permissions.BasePermission):
    """
    Coordenadores podem tudo.
    Professores podem acessar apenas as próprias aulas/sessões.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ["TEACHER", "COORDINATOR"]

    def has_object_permission(self, request, view, obj):
        # Coordenador tem acesso total
        if request.user.role == "COORDINATOR":
            return True

        # Professor pode mexer apenas nas sessões onde ele é o professor
        if request.user.role == "TEACHER":
            if hasattr(obj, "teacher"):  # para objetos do tipo ClassSession
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
