from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "products"

router = DefaultRouter()
router.register("products", views.ProductViewSet, basename="product")

urlpatterns = [path("", include(router.urls))]
