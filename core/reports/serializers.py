from rest_framework import serializers
from core.models import AttendanceRecord, Student, ClassRoom

class StudentAttendanceReportSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    student_name = serializers.CharField()
    total_classes = serializers.IntegerField()
    presents = serializers.IntegerField()
    absences = serializers.IntegerField()
    attendance_rate = serializers.FloatField()
