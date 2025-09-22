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
