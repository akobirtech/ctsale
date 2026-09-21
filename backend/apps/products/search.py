"""Qidiruv mantiqi — view'dan ajratilgan.

Sababi: bir xil qidiruvni sayt API'si ham, Telegram bot ham ishlatadi.
Mantiq view ichida qolsa, bot uni takrorlashga majbur bo'lardi va
ikkalasi vaqt o'tib bir-biridan uzoqlashardi.
"""

from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import F, Q

from .models import Product

# Undan qisqa so'rov shovqin beradi: "hp" hamma joyda uchraydi.
MIN_SEARCH_LENGTH = 2

# Trigram o'xshashligi chegarasi. Past qo'yilsa butunlay begona
# natijalar chiqadi, yuqori qo'yilsa opechatka kechirilmaydi.
TRIGRAM_THRESHOLD = 0.2
SUGGESTION_THRESHOLD = 0.15


def search_products(queryset, query):
    """Avval full-text, natija bo'lmasa trigram (opechatka uchun)."""
    search_query = SearchQuery(query, config="simple")
    ranked = (
        queryset.filter(search_vector=search_query)
        .annotate(rank=SearchRank(F("search_vector"), search_query))
        .order_by("-is_featured", "-rank", "-published_at")
    )
    if ranked.exists():
        return ranked

    return (
        queryset.annotate(similarity=TrigramSimilarity("title", query))
        .filter(
            Q(similarity__gt=TRIGRAM_THRESHOLD)
            | Q(title__icontains=query)
            | Q(model_name__icontains=query)
        )
        .order_by("-is_featured", "-similarity", "-published_at")
    )


def search_suggestions(query, limit=5):
    """Natija bo'lmaganda yaqin so'rovlarni taklif qilamiz."""
    similar = (
        Product.objects.public()
        .annotate(similarity=TrigramSimilarity("title", query))
        .filter(similarity__gt=SUGGESTION_THRESHOLD)
        .order_by("-similarity")
        .values_list("title", flat=True)[:limit]
    )
    return list(similar)
