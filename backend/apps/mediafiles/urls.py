"""Media yo'llari mahsulot ostida joylashadi:

    /api/v1/products/{slug}/images/
    /api/v1/products/{slug}/videos/
"""

from django.urls import path

from .views import ProductImageViewSet, ProductVideoViewSet

app_name = "mediafiles"

image_list = ProductImageViewSet.as_view({"get": "list", "post": "create"})
image_detail = ProductImageViewSet.as_view({"get": "retrieve", "delete": "destroy"})
image_primary = ProductImageViewSet.as_view({"post": "set_primary"})
image_reorder = ProductImageViewSet.as_view({"post": "reorder"})

video_list = ProductVideoViewSet.as_view({"get": "list", "post": "create"})
video_detail = ProductVideoViewSet.as_view({"get": "retrieve", "delete": "destroy"})

urlpatterns = [
    path("products/<slug:product_slug>/images/", image_list, name="image-list"),
    path("products/<slug:product_slug>/images/reorder/", image_reorder, name="image-reorder"),
    path("products/<slug:product_slug>/images/<int:pk>/", image_detail, name="image-detail"),
    path(
        "products/<slug:product_slug>/images/<int:pk>/set-primary/",
        image_primary,
        name="image-set-primary",
    ),
    path("products/<slug:product_slug>/videos/", video_list, name="video-list"),
    path("products/<slug:product_slug>/videos/<int:pk>/", video_detail, name="video-detail"),
]
