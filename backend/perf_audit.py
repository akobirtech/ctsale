"""Asosiy endpointlarda SQL so'rovlar sonini va vaqtini o'lchaydi."""
import os, sys, time, django
sys.path.insert(0, '.')
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings.dev'
django.setup()

from django.db import connection, reset_queries
from django.test import Client
from django.conf import settings

settings.DEBUG = True  # so'rovlarni yozib borish uchun
client = Client()

CASES = [
    ("Bosh sahifa bloklari", "/api/v1/products/featured/?limit=8"),
    ("Katalog (24 ta)",      "/api/v1/products/?page_size=24"),
    ("Katalog + facet",      "/api/v1/products/?page_size=24&facets=true"),
    ("Kategoriya + facet",   "/api/v1/products/?category=noutbuklar&facets=true"),
    ("Kategoriya daraxti",   "/api/v1/categories/tree/"),
    ("Qidiruv",              "/api/v1/products/search/?q=noutbuk"),
    ("Sitemap (105 URL)",    "/sitemap-products-uz-1.xml"),
]

from apps.products.models import Product
slug = Product.objects.public().first().slug
CASES.append(("Mahsulot sahifasi", f"/api/v1/products/{slug}/"))
CASES.append(("O'xshash mahsulotlar", f"/api/v1/products/{slug}/similar/"))

print(f"{'ENDPOINT':26} {'SO\'ROV':>7} {'VAQT':>9}  {'HOLAT':>5}")
print("-" * 56)
results = []
for name, url in CASES:
    client.get(url)          # keshni isitish
    reset_queries()
    start = time.perf_counter()
    response = client.get(url)
    elapsed = (time.perf_counter() - start) * 1000
    count = len(connection.queries)
    results.append((name, url, count, elapsed))
    flag = "!!" if count > 15 else ("!" if count > 10 else "")
    print(f"{name:26} {count:7} {elapsed:8.0f}ms  {response.status_code:5} {flag}")

print()
worst = max(results, key=lambda r: r[2])
print(f"Eng ko'p so'rov: {worst[0]} — {worst[2]} ta")
reset_queries()
client.get(worst[1])
from collections import Counter
sqls = Counter(q['sql'][:90] for q in connection.queries)
print("Takrorlanadigan so'rovlar:")
for sql, n in sqls.most_common(5):
    if n > 1:
        print(f"  {n}x  {sql}")
