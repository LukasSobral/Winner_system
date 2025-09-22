from django.urls import path
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.api_views import TeacherViewSet, ping, protected_ping, MeView, StudentViewSet,ClassroomViewSet,SessionViewSet,TeacherUnavailabilityViewSet

router = DefaultRouter()
router.register(r"teachers", TeacherViewSet, basename="teacher")
router.register(r"students", StudentViewSet, basename="student")
router.register(r"classrooms", ClassroomViewSet, basename="classroom")
router.register(r"sessions", SessionViewSet, basename="session")
router.register("teacher-unavailabilities", TeacherUnavailabilityViewSet, basename="teacher-unavailability")

urlpatterns = router.urls
urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("me/", MeView.as_view(), name="api_me"),
]

urlpatterns += router.urls
