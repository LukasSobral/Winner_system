from django.urls import path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from core.api_views import (
    TeacherViewSet,
    ping,
    protected_ping,
    MeView,
    StudentViewSet,
    ClassroomViewSet,
    SessionViewSet,
    TeacherUnavailabilityViewSet,
    SessionAuditLogViewSet
)
from . import api_views
from core.reports.teacher_reports import teacher_attendance_report
from core.reports.overview_reports import overview_report
from core.reports.views import ReportViewSet


router = DefaultRouter()
router.register(r"teachers", TeacherViewSet, basename="teacher")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"classrooms", ClassroomViewSet, basename="classroom")
router.register(r"sessions", SessionViewSet, basename="session")
router.register(r"teacher-unavailabilities", TeacherUnavailabilityViewSet, basename="teacher-unavailability")
router.register(r"reports/classroom", ReportViewSet, basename="report-classroom")

router.register(r"session-logs", SessionAuditLogViewSet, basename="session-log")

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("me/", MeView.as_view(), name="api_me"),

    # Rotas de teste de permissões
    path("test/coordinator/", api_views.test_coordinator, name="test_coordinator"),
    path("test/teacher-or-coordinator/", api_views.test_teacher_or_coordinator, name="test_teacher_or_coordinator"),
    path("test/student/", api_views.test_student, name="test_student"),

    # Relatórios adicionais
    path("reports/teacher/<int:pk>/attendance/", teacher_attendance_report, name="teacher_attendance_report"),
    path("reports/overview/", overview_report, name="overview_report"),
]

urlpatterns += router.urls
