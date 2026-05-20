from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .api_views import (
    ChangePasswordAPIView,
    ChoicesAPIView,
    DashboardAPIView,
    MatchViewSet,
    MeAPIView,
    PlayerViewSet,
    RegisterAPIView,
    ReportPrintAPIView,
    ReportsAPIView,
    SettingsAPIView,
    StatisticsAPIView,
    TrainingAttendanceViewSet,
    TrainingViewSet,
    UzbekTokenObtainPairView,
)

router = DefaultRouter()
router.register("players", PlayerViewSet, basename="api-players")
router.register("trainings", TrainingViewSet, basename="api-trainings")
router.register("attendance", TrainingAttendanceViewSet, basename="api-attendance")
router.register("matches", MatchViewSet, basename="api-matches")

urlpatterns = [
    path("auth/login/", UzbekTokenObtainPairView.as_view(), name="api-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="api-token-refresh"),
    path("auth/register/", RegisterAPIView.as_view(), name="api-register"),
    path("auth/me/", MeAPIView.as_view(), name="api-me"),
    path("settings/", SettingsAPIView.as_view(), name="api-settings"),
    path("settings/password/", ChangePasswordAPIView.as_view(), name="api-change-password"),
    path("choices/", ChoicesAPIView.as_view(), name="api-choices"),
    path("dashboard/", DashboardAPIView.as_view(), name="api-dashboard"),
    path("statistics/", StatisticsAPIView.as_view(), name="api-statistics"),
    path("reports/", ReportsAPIView.as_view(), name="api-reports"),
    path("reports/print/", ReportPrintAPIView.as_view(), name="api-reports-print"),
    path("", include(router.urls)),
]
