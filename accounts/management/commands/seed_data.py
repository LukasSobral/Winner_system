# core/management/commands/seed_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from core.models import ClassRoom, Student, ClassSession, AttendanceRecord


class Command(BaseCommand):
    help = "Popula o banco com dados iniciais (usuários, turmas, alunos, sessões, presenças)."

    def handle(self, *args, **kwargs):
        # Coordenador
        coordinator, _ = User.objects.get_or_create(
            username="coordinator",
            defaults={"email": "coordinator@example.com", "role": "COORDINATOR"}
        )
        coordinator.set_password("123456")
        coordinator.save()

        # Professores
        teacher1, _ = User.objects.get_or_create(
            username="teacher1",
            defaults={"email": "teacher1@example.com", "role": "TEACHER"}
        )
        teacher1.set_password("123456")
        teacher1.save()

        teacher2, _ = User.objects.get_or_create(
            username="teacher2",
            defaults={"email": "teacher2@example.com", "role": "TEACHER"}
        )
        teacher2.set_password("123456")
        teacher2.save()

        # Turmas
        classroom1, _ = ClassRoom.objects.get_or_create(name="TL Kimberley", book_level="11", schedule="19:00")
        classroom2, _ = ClassRoom.objects.get_or_create(name="TL Lucas", book_level="9", schedule="18:00")

        # Alunos
        for i in range(1, 6):
            Student.objects.get_or_create(
                full_name=f"Aluno {i}",
                classroom=classroom1 if i <= 3 else classroom2
            )

        # Sessões (próximos 5 dias)
        today = timezone.now().date()
        for i in range(5):
            session, _ = ClassSession.objects.get_or_create(
                classroom=classroom1 if i % 2 == 0 else classroom2,
                teacher=teacher1 if i % 2 == 0 else teacher2,
                date=today + timedelta(days=i),
                time="19:00" if i % 2 == 0 else "18:00",
                status="SCHEDULED",
            )

            # Criar registros de presença para cada aluno da turma da sessão
            students = Student.objects.filter(classroom=session.classroom)
            for student in students:
                AttendanceRecord.objects.get_or_create(
                    session=session,
                    student=student,
                    defaults={"present": False}  # padrão: ausência
                )

        self.stdout.write(self.style.SUCCESS("✅ Seed data criado com sucesso (incluindo chamadas)."))
