"""SEO yo'llari — sayt ildizida (til prefiksisiz), API ostida emas.

Qidiruv tizimlari robots.txt va sitemap.xml ni aynan ildizdan kutadi.
"""

from django.urls import path, re_path

from . import views

app_name = "seo"

urlpatterns = [
    path("robots.txt", views.robots_txt, name="robots"),
    path("sitemap.xml", views.sitemap_index, name="sitemap-index"),
    re_path(r"^sitemap-(?P<lang>[a-z]{2})\.xml$", views.sitemap_language, name="sitemap-lang"),
    re_path(r"^sitemap-pages-(?P<lang>[a-z]{2})\.xml$", views.sitemap_pages, name="sitemap-pages"),
    re_path(
        r"^sitemap-categories-(?P<lang>[a-z]{2})\.xml$",
        views.sitemap_categories,
        name="sitemap-categories",
    ),
    re_path(
        r"^sitemap-products-(?P<lang>[a-z]{2})-(?P<page>\d+)\.xml$",
        views.sitemap_products,
        name="sitemap-products",
    ),
]
