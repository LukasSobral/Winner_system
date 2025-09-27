from rest_framework import serializers
from core.models import Student,AttendanceRecord,ClassSession,ClassRoom,TeacherUnavailability, SessionAuditLog
from accounts.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]
        read_only_fields = ["id", "username", "role"]

class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password"]

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user

class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "first_name", "last_name", "email"]
        read_only_fields = ["id", "username"]

class TeacherCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password"]

    def create(self, validated_data):
        validated_data["role"] = "TEACHER"
        user = User.objects.create_user(**validated_data)
        return user

class StudentSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)

    class Meta:
        model = Student
        fields = ["id", "full_name", "classroom", "classroom_name", "active"]

class ClassroomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassRoom
        fields = ["id", "name", "schedule", "book_level"]

class SessionSerializer(serializers.ModelSerializer):
    classroom_name = serializers.CharField(source="classroom.name", read_only=True)
    teacher_name = serializers.CharField(source="teacher.get_full_name", read_only=True)
    substitute_name = serializers.CharField(source="substitute_teacher.get_full_name", read_only=True)

    class Meta:
        model = ClassSession
        fields = [
            "id",
            "classroom", "classroom_name",
            "date", "time",
            "teacher", "teacher_name",
            "substitute_teacher", "substitute_name",
            "status",
        ]

class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "student",
            "student_name",
            "present",
            "punctual",
            "uniform",
            "book",
            "repost",
        ]

class TeacherUnavailabilitySerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source="teacher.get_full_name", read_only=True)

    class Meta:
        model = TeacherUnavailability
        fields = ["id", "teacher", "teacher_name", "start_date", "end_date", "reason"]

class SessionAuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.get_full_name", read_only=True)
    session_name = serializers.CharField(source="session.__str__", read_only=True)

    class Meta:
        model = SessionAuditLog
        fields = ["id", "session_name", "user_name", "action", "timestamp", "changes"]
