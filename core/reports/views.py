from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

from core.models import ClassRoom, AttendanceRecord, Student,ClassSession
from accounts.permissions import IsCoordinatorOrReadOnly
from .serializers import StudentAttendanceReportSerializer

from core.reports.export_utils import export_to_csv



class ReportViewSet(viewsets.ViewSet):
    """
    ViewSet de relatórios relacionados a turmas.
    """
    permission_classes = [IsAuthenticated, IsCoordinatorOrReadOnly]

    @action(detail=True, methods=["get"], url_path="attendance")
    def classroom_attendance(self, request, pk=None):
        """
        Retorna relatório de presença dos alunos de uma turma (JSON).
        """
        classroom = get_object_or_404(ClassRoom, pk=pk)
        students = Student.objects.filter(classroom=classroom)

        total_classes = (
            AttendanceRecord.objects.filter(
                student__in=students, session__classroom=classroom
            )
            .values("session")
            .distinct()
            .count()
        )

        report_data = []
        for student in students:
            records = AttendanceRecord.objects.filter(
                student=student, session__classroom=classroom
            )
            presents = records.filter(present=True).count()
            absences = records.filter(present=False).count()
            rate = (presents / total_classes * 100) if total_classes > 0 else 0.0

            report_data.append({
                "student_id": student.id,
                "student_name": student.full_name,
                "total_classes": total_classes,
                "presents": presents,
                "absences": absences,
                "attendance_rate": round(rate, 2),
            })

        serializer = StudentAttendanceReportSerializer(report_data, many=True)
        return Response({
            "classroom": classroom.name,
            "total_classes": total_classes,
            "students": serializer.data
        })

    @action(detail=True, methods=["get"], url_path="attendance/export")
    def export_csv(self, request, pk=None):
        """
        Exporta o relatório de presenças da turma em CSV.
        """
        classroom = get_object_or_404(ClassRoom, pk=pk)
        students = Student.objects.filter(classroom=classroom)
        sessions = ClassSession.objects.filter(classroom=classroom)

        rows = []
        for student in students:
            records = AttendanceRecord.objects.filter(session__in=sessions, student=student)
            total_classes = records.count()
            presents = records.filter(present=True).count()
            absences = total_classes - presents
            rate = (presents / total_classes * 100) if total_classes > 0 else 0
            rows.append([
                student.id,
                student.full_name,
                total_classes,
                presents,
                absences,
                f"{rate:.2f}%"
            ])

        header = ["ID", "Aluno", "Total Aulas", "Presentes", "Faltas", "% Presença"]
        return export_to_csv(f"classroom_{pk}_attendance", header, rows)
