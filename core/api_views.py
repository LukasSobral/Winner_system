from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import viewsets, permissions,filters
from core.api_serializers import UserSerializer, UserUpdateSerializer,TeacherSerializer, TeacherCreateSerializer, StudentSerializer,ClassroomSerializer, SessionSerializer,AttendanceSerializer,TeacherUnavailabilitySerializer,SessionAuditLogSerializer
from core.models import Student, ClassRoom,ClassSession,AttendanceRecord,TeacherUnavailability,SessionAuditLog
from accounts.models import User
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework import status as drf_status

from accounts.permissions import IsCoordinator, IsTeacherOrCoordinator,IsStudentItself


@api_view(["GET"])
def ping(request):
    return Response({"message": "API funcionando!"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def protected_ping(request):
    return Response({"message": f"Olá {request.user.username}, você está autenticado!"})

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(request=UserUpdateSerializer, responses=UserSerializer)
    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(role="TEACHER")

    # Apenas coordenadores podem gerenciar professores
    permission_classes = [permissions.IsAuthenticated, IsCoordinator]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id", "username", "email"]
    search_fields = ["username", "first_name", "last_name", "email"]
    ordering_fields = ["id", "username", "first_name", "last_name", "email"]
    ordering = ["id"]

    def get_serializer_class(self):
        if self.action == "create":
            return TeacherCreateSerializer
        return TeacherSerializer


class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all().select_related("classroom")
    serializer_class = StudentSerializer

    # Apenas coordenadores podem gerenciar alunos
    permission_classes = [permissions.IsAuthenticated, IsCoordinator]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id", "classroom", "active"]
    search_fields = ["full_name", "classroom__name"]
    ordering_fields = ["id", "full_name", "classroom__name"]
    ordering = ["id"]


class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = ClassRoom.objects.all()
    serializer_class = ClassroomSerializer

    # Apenas coordenadores podem gerenciar turmas
    permission_classes = [permissions.IsAuthenticated, IsCoordinator]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id", "name", "book_level"]
    search_fields = ["name", "book_level"]
    ordering_fields = ["id", "name", "schedule", "book_level"]
    ordering = ["id"]


class SessionViewSet(viewsets.ModelViewSet):
    queryset = ClassSession.objects.all().select_related("classroom", "teacher", "substitute_teacher")
    serializer_class = SessionSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["classroom", "teacher", "status", "date"]
    search_fields = ["classroom__name", "teacher__first_name", "teacher__last_name"]
    ordering_fields = ["date", "time", "classroom__name", "teacher__first_name"]
    ordering = ["date", "time"]


    @action(detail=True, methods=["get"], url_path="attendance", permission_classes=[permissions.IsAuthenticated, IsTeacherOrCoordinator])
    def list_attendance(self, request, pk=None):
        """Lista os alunos da turma da sessão + status de presença"""
        session = self.get_object()
        students = Student.objects.filter(classroom=session.classroom)


        for student in students:
            AttendanceRecord.objects.get_or_create(session=session, student=student)

        attendance = AttendanceRecord.objects.filter(session=session).select_related("student")
        serializer = AttendanceSerializer(attendance, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"], url_path="attendance", permission_classes=[permissions.IsAuthenticated, IsTeacherOrCoordinator])
    def update_attendance(self, request, pk=None):
        """Atualiza presença dos alunos de uma sessão"""
        session = self.get_object()
        data = request.data

        if not isinstance(data, list):
            return Response({"error": "Esperada uma lista de presenças."}, status=400)

        updated = []
        for item in data:
            try:
                record = AttendanceRecord.objects.get(session=session, student_id=item["student"])
                serializer = AttendanceSerializer(record, data=item, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    updated.append(serializer.data)
                else:
                    return Response(serializer.errors, status=400)
            except AttendanceRecord.DoesNotExist:
                return Response({"error": f"Aluno {item['student']} não encontrado na chamada."}, status=404)

        return Response(updated, status=200)
    
    # --- NOVO ENDPOINT ---
    @action(detail=True, methods=["patch"], url_path="status", permission_classes=[permissions.IsAuthenticated, IsTeacherOrCoordinator])
    def update_status(self, request, pk=None):
        """Atualiza apenas o status da sessão"""
        session = self.get_object()
        new_status = request.data.get("status")

        if new_status not in ["SCHEDULED", "COMPLETED", "CANCELLED"]:
            return Response(
                {"error": "Status inválido. Use: SCHEDULED, COMPLETED ou CANCELLED."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        session.status = new_status
        session.save()

        serializer = self.get_serializer(session)
        return Response(serializer.data, status=drf_status.HTTP_200_OK)


    # -------------------------------
    # CREATE
    # -------------------------------
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        date = serializer.validated_data["date"]
        time = serializer.validated_data["time"]
        teacher = serializer.validated_data.get("teacher")
        classroom = serializer.validated_data.get("classroom")

        # 🔹 Validação: professor ocupado no mesmo horário
        if teacher and ClassSession.objects.filter(teacher=teacher, date=date, time=time).exists():
            return Response(
                {"error": f"O professor {teacher.get_full_name()} já possui outra aula neste horário."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 🔹 Validação: turma ocupada no mesmo horário
        if classroom and ClassSession.objects.filter(classroom=classroom, date=date, time=time).exists():
            return Response(
                {"error": f"A turma {classroom.name} já possui outra aula neste horário."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 🔹 Validação: professor indisponível
        if teacher and TeacherUnavailability.objects.filter(
            teacher=teacher,
            start_date__lte=date,
            end_date__gte=date
        ).exists():
            return Response(
                {"error": f"O professor {teacher.get_full_name()} está indisponível em {date}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().create(request, *args, **kwargs)

    
    # -------------------------------
    # UPDATE
    # -------------------------------
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        date = serializer.validated_data.get("date", instance.date)
        time = serializer.validated_data.get("time", instance.time)
        teacher = serializer.validated_data.get("teacher", instance.teacher)
        classroom = serializer.validated_data.get("classroom", instance.classroom)

        # 🔹 Validação: professor ocupado
        if teacher and ClassSession.objects.exclude(id=instance.id).filter(teacher=teacher, date=date, time=time).exists():
            return Response(
                {"error": f"O professor {teacher.get_full_name()} já possui outra aula neste horário."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 🔹 Validação: turma ocupada
        if classroom and ClassSession.objects.exclude(id=instance.id).filter(classroom=classroom, date=date, time=time).exists():
            return Response(
                {"error": f"A turma {classroom.name} já possui outra aula neste horário."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 🔹 Validação: professor indisponível
        if teacher and TeacherUnavailability.objects.filter(
            teacher=teacher,
            start_date__lte=date,
            end_date__gte=date
        ).exists():
            return Response(
                {"error": f"O professor {teacher.get_full_name()} está indisponível em {date}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(request, *args, **kwargs)


class TeacherUnavailabilityViewSet(viewsets.ModelViewSet):
    queryset = TeacherUnavailability.objects.all().select_related("teacher")
    serializer_class = TeacherUnavailabilitySerializer
    permission_classes = [permissions.IsAuthenticated, IsCoordinator]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["teacher", "start_date", "end_date"]
    search_fields = ["teacher__first_name", "teacher__last_name", "reason"]
    ordering_fields = ["start_date", "end_date"]
    ordering = ["-start_date"]


#============ Teste de rotas protegidas ============
@api_view(["GET"])
@permission_classes([IsCoordinator])
def test_coordinator(request):
    return Response({"msg": f"✅ Olá {request.user.username}, você é Coordenador!"})


@api_view(["GET"])
@permission_classes([IsTeacherOrCoordinator])
def test_teacher_or_coordinator(request):
    return Response({"msg": f"✅ Olá {request.user.username}, você é Professor ou Coordenador!"})


@api_view(["GET"])
@permission_classes([IsStudentItself])
def test_student(request):
    return Response({"msg": f"✅ Olá {request.user.username}, você acessou como Estudante!"})


class SessionAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SessionAuditLog.objects.all().select_related("session", "user")
    serializer_class = SessionAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Coordenador pode ver tudo
        if self.request.user.role == "COORDINATOR":
            return self.queryset
        # Professor só vê logs das suas sessões
        if self.request.user.role == "TEACHER":
            return self.queryset.filter(session__teacher=self.request.user)
        return SessionAuditLog.objects.none()