from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions, status
from rest_framework.response import Response

from accounts.models import User
from accounts.permissions import IsCoordinator
from core.models import ClassSession, ClassRoom, Student, AttendanceRecord


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated, IsCoordinator])
def teacher_attendance_report(request, pk: int):
    """
    Relatório consolidado por professor:
    - lista as turmas em que ele leciona,
    - total de aulas por turma,
    - presença/ausência por aluno da turma.
    """
    teacher = get_object_or_404(User, pk=pk, role="TEACHER")

    sessions = ClassSession.objects.filter(teacher=teacher)
    classrooms = ClassRoom.objects.filter(classsession__in=sessions).distinct()

    payload = {
        "teacher": teacher.get_full_name() or teacher.username,
        "teacher_id": teacher.id,
        "total_classes": sessions.count(),
        "classrooms": [],
    }

    for classroom in classrooms:
        classroom_sessions = sessions.filter(classroom=classroom)
        total_classes = classroom_sessions.count()

        students_data = []
        for student in Student.objects.filter(classroom=classroom):
            records = AttendanceRecord.objects.filter(session__in=classroom_sessions, student=student)

            presents = sum(1 for r in records if r.present)
            absences = sum(1 for r in records if not r.present)

            students_data.append({
                "student_id": student.id,
                "student_name": student.full_name,
                "presents": presents,
                "absences": absences,
                "attendance_rate": round((presents / total_classes) * 100, 2) if total_classes else 0,
            })

        payload["classrooms"].append({
            "classroom_id": classroom.id,
            "classroom_name": classroom.name,
            "total_classes": total_classes,
            "students": students_data,
        })

    return Response(payload, status=status.HTTP_200_OK)
