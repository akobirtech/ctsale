from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ModerationViewSet

app_name = "moderation"

router = DefaultRouter()
router.register("moderation", ModerationViewSet, basename="moderation")

urlpatterns = [path("", include(router.urls))]
