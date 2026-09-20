"""SEO ma'lumotlarini yig'ish: meta teglar, hreflang, canonical, JSON-LD.

Frontend (SSR) shu ma'lumotni olib `<head>` ga joylaydi. Mantiq
backendda turishi muhim: shunda sitemap, Telegram posti va sahifa
bir xil manbadan foydalanadi va bir-biriga zid bo'lmaydi.
"""

from django.conf import settings

from .models import SeoSettings


def _site_url():
    return settings.FRONTEND_URL.rstrip("/")


def hreflang_links(path):
    """Berilgan yo'l (til prefiksisiz) uchun barcha til variantlari.

    `x-default` standart tilga ishora qiladi — Google qaysi versiyani
    ko'rsatishni bilmagan holatlar uchun.
    """
    path = "/" + path.strip("/") if path.strip("/") else ""
    base = _site_url()
    links = [
        {"hreflang": lang, "href": f"{base}/{lang}{path}"}
        for lang in settings.SUPPORTED_LANGUAGES
    ]
    links.append(
        {"hreflang": "x-default", "href": f"{base}/{settings.DEFAULT_LANGUAGE}{path}"}
    )
    return links


def verification_tags():
    """Google/Yandex/Bing tasdiqlash meta teglari.

    Avval admin panelidagi qiymat, bo'lmasa `.env`. Kodda hech qachon
    qat'iy yozilmaydi.
    """
    config = SeoSettings.load()
    tags = {}
    pairs = [
        ("google-site-verification", config.google_site_verification, settings.GOOGLE_SITE_VERIFICATION),
        ("yandex-verification", config.yandex_verification, settings.YANDEX_VERIFICATION),
        ("msvalidate.01", config.bing_verification, settings.BING_VERIFICATION),
    ]
    for name, from_db, from_env in pairs:
        value = (from_db or from_env or "").strip()
        if value:
            tags[name] = value
    return tags


def site_allows_indexing():
    return settings.SEO_ALLOW_INDEXING and SeoSettings.load().robots_allow_indexing


# --------------------------------------------------------------------------
# Mahsulot
# --------------------------------------------------------------------------
def product_seo_payload(product, lang=None):
    """Mahsulot sahifasi uchun to'liq SEO to'plami."""
    lang = lang if lang in settings.SUPPORTED_LANGUAGES else settings.DEFAULT_LANGUAGE
    config = SeoSettings.load()
    base = _site_url()
    path = f"/product/{product.slug}"
    canonical = f"{base}/{lang}{path}"

    indexable = product.should_be_indexed and site_allows_indexing()

    image_url = _primary_image_url(product) or _default_og_image(config, base)

    return {
        "title": product.seo_title or f"{product.title} — {config.site_name}",
        "description": product.seo_description or config.default_description,
        "keywords": product.seo_keywords,
        "canonical": canonical,
        "robots": "index, follow" if indexable else "noindex, follow",
        "hreflang": hreflang_links(path),
        "og": {
            "type": "product",
            "title": product.og_title or product.seo_title or product.title,
            "description": product.og_description or product.seo_description,
            "url": canonical,
            "image": image_url,
            "site_name": config.site_name,
            "locale": {"uz": "uz_UZ", "ru": "ru_RU", "en": "en_US"}[lang],
        },
        "twitter": {
            "card": "summary_large_image",
            "title": product.og_title or product.title,
            "description": product.og_description or product.seo_description,
            "image": image_url,
        },
        "jsonld": [
            product_jsonld(product, canonical, image_url, config),
            breadcrumb_jsonld(product, lang, base),
        ],
    }


def _primary_image_url(product):
    image = product.primary_image
    if image is None:
        return None
    target = image.large or image.medium or image.image
    if not target:
        return None
    url = target.url
    return url if url.startswith("http") else f"{_site_url()}{url}"


def _default_og_image(config, base):
    if config.default_og_image:
        url = config.default_og_image.url
        return url if url.startswith("http") else f"{base}{url}"
    return f"{base}/og-default.png"


def product_jsonld(product, canonical, image_url, config=None):
    """schema.org/Product + Offer."""
    config = config or SeoSettings.load()

    offer = {
        "@type": "Offer",
        "url": canonical,
        "availability": product.schema_availability,
        "itemCondition": product.schema_condition,
        "priceCurrency": product.currency,
        "seller": {
            "@type": "Person",
            "name": product.seller.get_full_name() or "Sotuvchi",
        },
    }
    if product.price is not None:
        offer["price"] = str(product.price)
    if product.expires_at:
        offer["priceValidUntil"] = product.expires_at.date().isoformat()

    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.title,
        "description": (product.seo_description or product.description)[:500],
        "sku": str(product.id),
        "url": canonical,
        "offers": offer,
        "category": product.category.name_uz if product.category_id else None,
    }

    if image_url:
        data["image"] = [image_url]
    if product.brand_id:
        data["brand"] = {"@type": "Brand", "name": product.brand.name}
    if product.model_name:
        data["model"] = product.model_name

    # Sxemaga qo'shimcha xususiyatlar — qidiruv natijalarida boyroq
    # ko'rinish beradi.
    properties = [
        {"@type": "PropertyValue", "name": code, "value": str(value)}
        for code, value in list((product.specs or {}).items())[:12]
        if value not in (None, "", [])
    ]
    if properties:
        data["additionalProperty"] = properties

    return {k: v for k, v in data.items() if v is not None}


def breadcrumb_jsonld(product, lang, base=None):
    base = base or _site_url()
    items = [{"name": "Bosh sahifa", "path": ""}]

    if product.category_id:
        for category in product.category.ancestors(include_self=True):
            items.append({"name": category.name_uz, "path": f"/category/{category.slug}"})

    items.append({"name": product.title, "path": f"/product/{product.slug}"})

    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": index,
                "name": item["name"],
                "item": f"{base}/{lang}{item['path']}",
            }
            for index, item in enumerate(items, start=1)
        ],
    }


# --------------------------------------------------------------------------
# Sayt darajasi
# --------------------------------------------------------------------------
def organization_jsonld():
    config = SeoSettings.load()
    base = _site_url()

    data = {
        "@context": "https://schema.org",
        "@type": "Organization",
        "name": config.site_name,
        "url": base,
    }
    if config.organization_logo:
        data["logo"] = f"{base}{config.organization_logo.url}"
    if config.social_links:
        data["sameAs"] = config.social_links
    if config.organization_phone or config.organization_email:
        contact = {"@type": "ContactPoint", "contactType": "customer support"}
        if config.organization_phone:
            contact["telephone"] = config.organization_phone
        if config.organization_email:
            contact["email"] = config.organization_email
        data["contactPoint"] = [contact]
    return data


def website_jsonld(lang=None):
    """WebSite + SearchAction — Google qidiruv maydonchasini ko'rsatishi uchun."""
    lang = lang or settings.DEFAULT_LANGUAGE
    config = SeoSettings.load()
    base = _site_url()

    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": config.site_name,
        "url": base,
        "inLanguage": lang,
        "potentialAction": {
            "@type": "SearchAction",
            "target": {
                "@type": "EntryPoint",
                "urlTemplate": f"{base}/{lang}/search?q={{search_term_string}}",
            },
            "query-input": "required name=search_term_string",
        },
    }


def category_seo_payload(category, lang=None, page=1):
    lang = lang if lang in settings.SUPPORTED_LANGUAGES else settings.DEFAULT_LANGUAGE
    config = SeoSettings.load()
    base = _site_url()
    path = f"/category/{category.slug}"
    canonical = f"{base}/{lang}{path}"

    name = getattr(category, f"name_{lang}", "") or category.name_uz
    title = category.meta_title or f"{name} — {config.site_name}"
    description = category.meta_description or (
        f"{name}: yangi va ishlatilgan mahsulotlar. "
        f"{config.site_name} — IT texnika marketplace."
    )

    # 2-sahifadan boshlab canonical o'zining sahifasiga ishora qiladi,
    # lekin indekslanmaydi — duplicate content oldini olish uchun.
    robots = "index, follow" if page == 1 and site_allows_indexing() else "noindex, follow"

    return {
        "title": title[:200],
        "description": description[:300],
        "canonical": canonical if page == 1 else f"{canonical}?page={page}",
        "robots": robots,
        "hreflang": hreflang_links(path),
        "og": {
            "type": "website",
            "title": title,
            "description": description,
            "url": canonical,
            "image": _default_og_image(config, base),
            "site_name": config.site_name,
        },
        "jsonld": [website_jsonld(lang), organization_jsonld()],
    }
