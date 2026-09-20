from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "catalog"

router = DefaultRouter()
router.register("categories", views.CategoryViewSet, basename="category")
router.register("brands", views.BrandViewSet, basename="brand")
router.register("regions", views.RegionViewSet, basename="region")
router.register("attributes", views.AttributeViewSet, basename="attribute")

urlpatterns = [path("", include(router.urls))]
