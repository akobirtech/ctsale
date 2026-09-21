from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CompareViewSet, FavoriteViewSet, ReportViewSet

app_name = "interactions"

router = DefaultRouter()
router.register("favorites", FavoriteViewSet, basename="favorite")
router.register("compare", CompareViewSet, basename="compare")
router.register("reports", ReportViewSet, basename="report")

urlpatterns = [path("", include(router.urls))]
