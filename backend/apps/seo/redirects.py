"""Eski URL'larni yangisiga yo'naltirish — 301 / 302 / 410.

Nega kerak: slug o'zgarganda eski manzil indeksda qoladi. Agar u 404
bersa, sahifa yig'gan barcha SEO vazni yo'qoladi. 301 esa vaznni yangi
manzilga o'tkazadi.

Manba ikkita:
  1. `SeoRedirect` jadvali — admin qo'lda kiritadigan har qanday yo'l.
  2. `Product.previous_slugs` — slug o'zgarganda avtomatik saqlanadi.

Ikkinchisi avtomatik bo'lgani uchun jadvalga nusxa ko'chirilmaydi:
bitta haqiqat manbasi ikkita bo'lib qolmasligi kerak.
"""

from django.conf import settings
from django.core.cache import cache
from django.db.models import F

from .models import RedirectType, SeoRedirect

# Natija qisqa muddat keshlanadi: redirectlar kam o'zgaradi, lekin
# admin tahriri bir daqiqadan ko'p kutib turmasin.
CACHE_TTL = 60
CACHE_PREFIX = "seo:redirect:"

PRODUCT_PREFIX = "/product/"


def strip_language(path):
    """`/uz/product/x` -> `("uz", "/product/x")`. Prefiks bo'lmasa til None."""
    parts = path.split("/", 2)
    if len(parts) >= 2 and parts[1] in settings.SUPPORTED_LANGUAGES:
        rest = "/" + (parts[2] if len(parts) > 2 else "")
        return parts[1], rest.rstrip("/") or "/"
    return None, path.rstrip("/") or "/"


def _lookup_table(path):
    row = (
        SeoRedirect.objects.filter(old_path=path, is_active=True)
        .only("id", "new_path", "status_code")
        .first()
    )
    if row is None:
        return None

    # Hisoblagich: qaysi eski manzillar hali ham ishlatilayotganini
    # ko'rish uchun. F() — parallel so'rovlarda yo'qolmasligi uchun.
    SeoRedirect.objects.filter(pk=row.pk).update(hits=F("hits") + 1)

    if row.status_code == RedirectType.GONE or not row.new_path:
        return {"status": 410, "target": None}
    return {"status": int(row.status_code), "target": row.new_path}


def _lookup_product(path):
    """Eski slug yoki o'chirilgan e'lon uchun javob."""
    if not path.startswith(PRODUCT_PREFIX):
        return None

    from apps.products.models import PUBLIC_STATUSES, Product

    slug = path[len(PRODUCT_PREFIX) :].strip("/")
    if not slug or "/" in slug:
        return None

    moved = (
        Product.objects.filter(
            previous_slugs__contains=[slug],
            status__in=PUBLIC_STATUSES,
            is_deleted=False,
        )
        .values_list("slug", flat=True)
        .first()
    )
    if moved:
        return {"status": 301, "target": f"{PRODUCT_PREFIX}{moved}"}

    if Product.all_objects.filter(slug=slug, is_deleted=True).exists():
        return {"status": 410, "target": None}

    return None


def resolve(path):
    """Yo'l uchun redirect qaroni yoki None.

    Qaytadi: `{"status": 301|302|410, "target": "/yangi/yo'l"|None, "lang": "uz"|None}`
    """
    lang, clean = strip_language(path)

    key = f"{CACHE_PREFIX}{clean}"
    cached = cache.get(key)
    if cached is not None:
        # Bo'sh lug'at — "bu yo'lda redirect yo'q" degan keshlangan javob.
        result = cached or None
    else:
        result = _lookup_table(clean) or _lookup_product(clean)
        # Faqat "topilmadi" keshlanadi; topilgani hisoblagichni
        # yangilashi kerak, shuning uchun har safar bazaga boradi.
        if result is None:
            cache.set(key, {}, CACHE_TTL)

    if result is None:
        return None

    target = result["target"]
    if target and lang:
        target = f"/{lang}{target}"
    return {"status": result["status"], "target": target, "lang": lang}
