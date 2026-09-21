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
    # SEO fayllari sayt ildizida bo'lishi shart (til prefiksisiz)
    path("", include("apps.seo.urls")),
    path("django-admin/", admin.site.urls),
    path(API_V1, include("apps.core.urls")),
    path(f"{API_V1}auth/", include("apps.accounts.urls")),
    path(API_V1, include("apps.catalog.urls")),
    path(API_V1, include("apps.mediafiles.urls")),
    path(API_V1, include("apps.products.urls")),
    path(API_V1, include("apps.moderation.urls")),
    path(API_V1, include("apps.interactions.urls")),
    path(API_V1, include("apps.notifications.urls")),
    path(API_V1, include("apps.adminapi.urls")),
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
