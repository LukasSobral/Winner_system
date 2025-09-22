from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.views import APIView
from rest_framework import viewsets, permissions,filters
from core.api_serializers import UserSerializer, UserUpdateSerializer,TeacherSerializer, TeacherCreateSerializer, StudentSerializer,ClassroomSerializer, SessionSerializer,AttendanceSerializer
from core.models import User, Student, ClassRoom,ClassSession,AttendanceRecord
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework import status as drf_status

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
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["id", "classroom", "active"]
    search_fields = ["full_name", "classroom__name"]
    ordering_fields = ["id", "full_name", "classroom__name"]
    ordering = ["id"]

class ClassroomViewSet(viewsets.ModelViewSet):
    queryset = ClassRoom.objects.all()
    serializer_class = ClassroomSerializer
    permission_classes = [permissions.IsAuthenticated]

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


    @action(detail=True, methods=["get"], url_path="attendance")
    def list_attendance(self, request, pk=None):
        """Lista os alunos da turma da sessão + status de presença"""
        session = self.get_object()
        students = Student.objects.filter(classroom=session.classroom)

        # Garante que existam registros de presença para cada aluno
        for student in students:
            AttendanceRecord.objects.get_or_create(session=session, student=student)

        attendance = AttendanceRecord.objects.filter(session=session).select_related("student")
        serializer = AttendanceSerializer(attendance, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["patch"], url_path="attendance")
    def update_attendance(self, request, pk=None):
        """Atualiza presença dos alunos de uma sessão"""
        session = self.get_object()
        data = request.data  # deve ser uma lista de objetos

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
    @action(detail=True, methods=["patch"], url_path="status")
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


    def create(self, request, *args, **kwargs):
        """Validação customizada ao criar aula"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        date = serializer.validated_data["date"]
        time = serializer.validated_data["time"]
        teacher = serializer.validated_data.get("teacher")
        classroom = serializer.validated_data.get("classroom")

        # Validação professor ocupado
        if teacher and ClassSession.objects.filter(teacher=teacher, date=date, time=time).exists():
            return Response(
                {"error": f"O professor {teacher.get_full_name()} já possui outra aula neste horário."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Validação turma ocupada
        if classroom and ClassSession.objects.filter(classroom=classroom, date=date, time=time).exists():
            return Response(
                {"error": f"A turma {classroom.name} já possui outra aula neste horário."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Mesma validação ao atualizar"""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        date = serializer.validated_data.get("date", instance.date)
        time = serializer.validated_data.get("time", instance.time)
        teacher = serializer.validated_data.get("teacher", instance.teacher)
        classroom = serializer.validated_data.get("classroom", instance.classroom)

        if teacher and ClassSession.objects.exclude(id=instance.id).filter(teacher=teacher, date=date, time=time).exists():
            return Response(
                {"error": f"O professor {teacher.get_full_name()} já possui outra aula neste horário."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if classroom and ClassSession.objects.exclude(id=instance.id).filter(classroom=classroom, date=date, time=time).exists():
            return Response(
                {"error": f"A turma {classroom.name} já possui outra aula neste horário."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return super().update(request, *args, **kwargs)
    