"""Denormalizatsiya qilingan hisoblagichlarni qayta hisoblaydi.

Mahsulot statusi odatdagi yo'l bilan o'zgarganda hisoblagich
avtomatik yangilanadi. Bu komanda ommaviy import/seed yoki
qo'lda baza o'zgartirilgandan keyin ishlatiladi.
"""

from django.core.management.base import BaseCommand
from django.db.models import Count

from apps.catalog.models import Brand, Category
from apps.products.models import Product, ProductStatus


class Command(BaseCommand):
    help = "Kategoriya va brendlardagi mahsulot sonini qayta hisoblaydi."

    def handle(self, *args, **options):
        live = Product.objects.filter(status=ProductStatus.APPROVED)

        # Brend: to'g'ridan-to'g'ri sanash yetarli.
        by_brand = dict(
            live.exclude(brand__isnull=True)
            .values_list("brand_id")
            .annotate(total=Count("id"))
        )
        for brand in Brand.objects.all():
            Brand.objects.filter(pk=brand.pk).update(products_count=by_brand.get(brand.pk, 0))

        # Kategoriya: ota kategoriya avlodlarining yig'indisini ko'rsatadi,
        # shuning uchun har biri uchun daraxt bo'ylab sanaymiz.
        direct = dict(live.values_list("category_id").annotate(total=Count("id")))
        updated = 0
        for category in Category.objects.all():
            total = sum(direct.get(pk, 0) for pk in category.descendant_ids())
            Category.objects.filter(pk=category.pk).update(products_count=total)
            updated += 1

        top = Category.objects.filter(products_count__gt=0).order_by("-products_count")[:8]
        self.stdout.write(
            self.style.SUCCESS(
                f"{updated} kategoriya, {Brand.objects.count()} brend qayta hisoblandi"
            )
        )
        for category in top:
            self.stdout.write(f"  {category.name_uz:28} {category.products_count}")
