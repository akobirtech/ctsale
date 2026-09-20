"""CT Sale — asosiy URL routerlari.

Barcha API `/api/v1/` ostida. Versiyalash URL orqali: kelajakda v2
qo'shilganda v1 buzilmaydi.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

API_V1 = "api/v1/"

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path(API_V1, include("apps.core.urls")),
    path(f"{API_V1}auth/", include("apps.accounts.urls")),
]

# API hujjatlari
urlpatterns += [
    path(f"{API_V1}schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        f"{API_V1}docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        f"{API_V1}redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
