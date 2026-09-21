"""Dinamik robots.txt va sitemap.

Statik fayl emas: mahsulot qo'shilganda/o'chirilganda sitemap o'zi
yangilanadi va admin paneldagi sozlamalar darhol kuchga kiradi.

Nginx bu yo'llarni backendga uzatadi (DEPLOYMENT.md ga qarang):
    /robots.txt
    /sitemap.xml
    /sitemap-{uz,ru,en}.xml
    /sitemap-products-{lang}-{page}.xml
"""

from django.conf import settings
from django.http import Http404, HttpResponse
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_GET

from apps.catalog.models import Category
from apps.products.models import Product, ProductStatus

from .models import SeoSettings, StaticPageSeo
from .services import site_allows_indexing

XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'
XMLNS = "http://www.sitemaps.org/schemas/sitemap/0.9"
XHTML_NS = "http://www.w3.org/1999/xhtml"

# Sitemapga kiruvchi statik sahifalar: (yo'l, ustuvorlik, chastota)
STATIC_ROUTES = [
    ("", "1.0", "daily"),
    ("/catalog", "0.9", "daily"),
    ("/about", "0.3", "monthly"),
    ("/terms", "0.2", "yearly"),
    ("/privacy", "0.2", "yearly"),
]


def _base():
    return settings.FRONTEND_URL.rstrip("/")


def _escape(text):
    """XML uchun ekranlash — URL'larda & va ' uchrashi mumkin."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


# --------------------------------------------------------------------------
# robots.txt
# --------------------------------------------------------------------------
@require_GET
@cache_page(600)
def robots_txt(request):
    config = SeoSettings.load()
    base = _base()
    lines = []

    if not site_allows_indexing():
        # Staging/test nusxasi indeksga tushmasligi kerak — aks holda
        # asosiy sayt bilan duplicate content bo'ladi.
        lines += ["User-agent: *", "Disallow: /"]
        return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")

    disallow = [
        line.strip()
        for line in (config.robots_extra_disallow or "").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    lines += ["User-agent: *"]
    for path in disallow:
        # Barcha til prefikslari uchun ham yopamiz: /uz/profile, /ru/profile ...
        lines.append(f"Disallow: {path}")
        for lang in settings.SUPPORTED_LANGUAGES:
            lines.append(f"Disallow: /{lang}{path}")

    lines += [
        "",
        "# Qidiruv natijalari sahifalari indekslanmaydi (duplicate content)",
        "Disallow: /*?sort=",
        "Disallow: /*?page=",
        "Disallow: /*?spec_",
        "Allow: /*?page=1",
        "",
        "# Rasm va statik fayllar ochiq",
        "Allow: /media/",
        "Allow: /static/",
        "",
        "Crawl-delay: 1",
        "",
        # Yandex kanonik domenni aniq bilishi uchun
        "User-agent: Yandex",
        f"Host: {base.replace('https://', '').replace('http://', '')}",
        "",
        f"Sitemap: {base}/sitemap.xml",
    ]
    for lang in settings.SUPPORTED_LANGUAGES:
        lines.append(f"Sitemap: {base}/sitemap-{lang}.xml")

    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain; charset=utf-8")


# --------------------------------------------------------------------------
# sitemap.xml (indeks)
# --------------------------------------------------------------------------
@require_GET
@cache_page(settings.SITEMAP_CACHE_SECONDS)
def sitemap_index(request):
    base = _base()
    now = timezone.now().date().isoformat()

    entries = []
    for lang in settings.SUPPORTED_LANGUAGES:
        entries.append(f"{base}/sitemap-{lang}.xml")

    body = "".join(
        f"<sitemap><loc>{_escape(url)}</loc><lastmod>{now}</lastmod></sitemap>"
        for url in entries
    )
    xml = f'{XML_HEADER}<sitemapindex xmlns="{XMLNS}">{body}</sitemapindex>'
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")


@require_GET
@cache_page(settings.SITEMAP_CACHE_SECONDS)
def sitemap_language(request, lang):
    """Bitta til uchun sitemap indeksi: statik + kategoriya + mahsulot sahifalari."""
    if lang not in settings.SUPPORTED_LANGUAGES:
        raise Http404("Noma'lum til")

    base = _base()
    now = timezone.now().date().isoformat()
    page_size = settings.SITEMAP_PAGE_SIZE

    total = _indexable_products().count()
    pages = max(1, -(-total // page_size))  # yuqoriga yaxlitlash

    urls = [f"{base}/sitemap-pages-{lang}.xml", f"{base}/sitemap-categories-{lang}.xml"]
    urls += [f"{base}/sitemap-products-{lang}-{n}.xml" for n in range(1, pages + 1)]

    body = "".join(
        f"<sitemap><loc>{_escape(url)}</loc><lastmod>{now}</lastmod></sitemap>"
        for url in urls
    )
    xml = f'{XML_HEADER}<sitemapindex xmlns="{XMLNS}">{body}</sitemapindex>'
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")


# --------------------------------------------------------------------------
# Sitemap bo'limlari
# --------------------------------------------------------------------------
def _url_entry(path, lastmod=None, changefreq="weekly", priority="0.5", with_alternates=True):
    """Bitta <url> yozuvi, hreflang alternativalari bilan.

    hreflang'ni sitemap ichida berish Google tomonidan qo'llab-quvvatlanadi
    va `<head>` dagi teglarni dublikatlaydi — ikkalasi bir xil bo'lishi
    kerak, aks holda Google ziddiyatni e'tiborsiz qoldiradi.
    """
    base = _base()
    parts = [f"<loc>{_escape(base + path)}</loc>"]

    if with_alternates:
        # path "/uz/..." ko'rinishida — til qismini almashtiramiz.
        segments = path.split("/", 2)
        tail = f"/{segments[2]}" if len(segments) > 2 else ""
        for alt in settings.SUPPORTED_LANGUAGES:
            href = f"{base}/{alt}{tail}"
            parts.append(
                f'<xhtml:link rel="alternate" hreflang="{alt}" href="{_escape(href)}"/>'
            )
        default_href = f"{base}/{settings.DEFAULT_LANGUAGE}{tail}"
        parts.append(
            f'<xhtml:link rel="alternate" hreflang="x-default" href="{_escape(default_href)}"/>'
        )

    if lastmod:
        parts.append(f"<lastmod>{lastmod}</lastmod>")
    parts.append(f"<changefreq>{changefreq}</changefreq>")
    parts.append(f"<priority>{priority}</priority>")
    return f"<url>{''.join(parts)}</url>"


def _wrap(urls):
    xml = (
        f'{XML_HEADER}<urlset xmlns="{XMLNS}" xmlns:xhtml="{XHTML_NS}">'
        f'{"".join(urls)}</urlset>'
    )
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")


@require_GET
@cache_page(settings.SITEMAP_CACHE_SECONDS)
def sitemap_pages(request, lang):
    if lang not in settings.SUPPORTED_LANGUAGES:
        raise Http404
    if not site_allows_indexing():
        return _wrap([])

    overrides = {p.path: p for p in StaticPageSeo.objects.filter(is_indexable=True)}
    urls = []
    for path, priority, changefreq in STATIC_ROUTES:
        override = overrides.get(path or "/")
        if override is not None:
            priority = str(override.sitemap_priority)
            changefreq = override.changefreq
        urls.append(
            _url_entry(f"/{lang}{path}", changefreq=changefreq, priority=priority)
        )
    return _wrap(urls)


@require_GET
@cache_page(settings.SITEMAP_CACHE_SECONDS)
def sitemap_categories(request, lang):
    if lang not in settings.SUPPORTED_LANGUAGES:
        raise Http404
    if not site_allows_indexing():
        return _wrap([])

    urls = []
    for category in Category.objects.filter(is_active=True).order_by("order"):
        # Bo'sh kategoriya indeksga tushmasin — thin content.
        if category.products_count == 0:
            continue
        urls.append(
            _url_entry(
                f"/{lang}/category/{category.slug}",
                lastmod=category.updated_at.date().isoformat(),
                changefreq="daily",
                priority="0.8" if category.parent_id is None else "0.7",
            )
        )
    return _wrap(urls)


@require_GET
@cache_page(settings.SITEMAP_CACHE_SECONDS)
def sitemap_products(request, lang, page):
    if lang not in settings.SUPPORTED_LANGUAGES:
        raise Http404
    if not site_allows_indexing():
        return _wrap([])

    page = max(1, int(page))
    page_size = settings.SITEMAP_PAGE_SIZE
    offset = (page - 1) * page_size

    queryset = _indexable_products()[offset : offset + page_size]
    urls = [
        _url_entry(
            f"/{lang}/product/{slug}",
            lastmod=updated_at.date().isoformat(),
            changefreq="weekly",
            # Yangi va faol e'lonlar ustuvorroq.
            priority="0.9" if status == ProductStatus.APPROVED else "0.5",
        )
        for slug, updated_at, status in queryset.values_list("slug", "updated_at", "status")
    ]
    if not urls and page > 1:
        raise Http404("Bu sahifada URL yo'q")
    return _wrap(urls)


def _indexable_products():
    """Sitemapga kiradigan mahsulotlar.

    `should_be_indexed` Python xossasi — uni so'rovda ishlatib
    bo'lmaydi, shuning uchun shart shu yerda takrorlanadi.
    Sotilganlar sozlamaga qarab qo'shiladi.
    """
    config = SeoSettings.load()
    statuses = [ProductStatus.APPROVED, ProductStatus.RESERVED]
    if config.index_sold_products:
        statuses.append(ProductStatus.SOLD)

    return (
        Product.objects.filter(status__in=statuses, is_indexable=True)
        .order_by("-published_at", "-created_at")[: config.sitemap_products_limit]
    )
