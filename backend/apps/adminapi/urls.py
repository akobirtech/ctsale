from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import AdminUserViewSet, AuditLogViewSet, DashboardViewSet, TelegramAdminViewSet

app_name = "adminapi"

router = DefaultRouter()
router.register("dashboard", DashboardViewSet, basename="admin-dashboard")
router.register("users", AdminUserViewSet, basename="admin-user")
router.register("audit", AuditLogViewSet, basename="admin-audit")
router.register("telegram", TelegramAdminViewSet, basename="admin-telegram")

urlpatterns = [path("admin/", include(router.urls))]
