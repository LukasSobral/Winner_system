from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser

# Custom User
class User(AbstractUser):
    ROLE_CHOICES = [
        ('COORDINATOR', 'Coordinator'),
        ('TEACHER', 'Teacher'),
        ('STUDENT', 'Student'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    def __str__(self):
        return self.username

# Turma
class ClassRoom(models.Model):
    name = models.CharField(max_length=100)
    schedule = models.TimeField()
    book_level = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} - {self.schedule}"

# Aluno
class Student(models.Model):
    full_name = models.CharField(max_length=100)
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.full_name

# Sessão de Aula
class ClassSession(models.Model):
    classroom = models.ForeignKey(ClassRoom, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    teacher = models.ForeignKey(User, related_name='teacher_sessions', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'TEACHER'})
    substitute_teacher = models.ForeignKey(User, related_name='substitute_sessions', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'TEACHER'})
    
    STATUS_CHOICES = [
        ('SCHEDULED', 'Agendada'),
        ('COMPLETED', 'Concluída'),
        ('CANCELLED', 'Cancelada'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SCHEDULED')

    def get_responsible_teacher(self):
        return self.substitute_teacher if self.substitute_teacher else self.teacher

    def __str__(self):
        return f"{self.classroom.name} - {self.date} {self.time}"


# Registro de Presença
class AttendanceRecord(models.Model):
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    present = models.BooleanField(default=False)
    punctual = models.BooleanField(default=False)
    uniform = models.BooleanField(default=False)
    book = models.BooleanField(default=False)
    repost = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.full_name} - {self.session.date}"

class Holiday(models.Model):
    class Meta:
        verbose_name = "Feriado/Bloqueio"
        verbose_name_plural = "Feriados e Bloqueios"
        
    date = models.DateField(unique=True)
    description = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.date.strftime('%d/%m/%Y')} - {self.description}"


class SessionAuditLog(models.Model):
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)
    changes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.session} - {self.action} - {self.timestamp}"


class TeacherUnavailability(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'TEACHER'})
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.teacher.get_full_name()} indisponível de {self.start_date} até {self.end_date}"
