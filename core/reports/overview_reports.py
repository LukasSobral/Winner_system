from collections import defaultdict
from django.db.models import Count, Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response

from accounts.permissions import IsCoordinator
from core.models import ClassSession, ClassRoom, AttendanceRecord, Student, User


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsCoordinator])
def overview_report(request):
    """
    Visão geral do sistema:
    - contagem de usuários por papel
    - aulas por status
    - aulas por turma
    - ranking de presença por aluno (top 5)
    """
    # Usuários por papel
    roles = (
        User.objects.values("role")
        .annotate(total=Count("id"))
        .order_by()
    )
    users_by_role = {r["role"]: r["total"] for r in roles}

    # Aulas por status
    sessions_by_status = (
        ClassSession.objects.values("status")
        .annotate(total=Count("id"))
        .order_by()
    )
    sessions_by_status = {s["status"]: s["total"] for s in sessions_by_status}

    # Aulas por turma
    classes_by_classroom = (
        ClassRoom.objects
        .annotate(total_classes=Count("classsession"))
        .values("id", "name", "total_classes")
        .order_by("-total_classes", "name")
    )

    # Top 5 alunos por presença (percentual em todas as sessões da sua turma)
    top_students = []
    for student in Student.objects.select_related("classroom"):
        total_sessions = ClassSession.objects.filter(classroom=student.classroom).count()
        presents = AttendanceRecord.objects.filter(student=student, present=True).count()
        rate = round((presents / total_sessions) * 100, 2) if total_sessions else 0
        top_students.append((rate, {
            "student_id": student.id,
            "student_name": student.full_name,
            "classroom_id": student.classroom_id,
            "classroom_name": student.classroom.name,
            "attendance_rate": rate,
        }))
    top_students = [item for _, item in sorted(top_students, key=lambda x: x[0], reverse=True)[:5]]

    payload = {
        "users_by_role": users_by_role,
        "sessions_by_status": sessions_by_status,
        "classes_by_classroom": list(classes_by_classroom),
        "top_students_by_attendance": top_students,
    }
    return Response(payload, status=status.HTTP_200_OK)
