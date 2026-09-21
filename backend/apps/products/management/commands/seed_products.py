"""Demo foydalanuvchilar va mahsulotlarni yaratadi.

Rasmlar Pillow bilan generatsiya qilinadi: internetdan olingan
suratlar litsenziya jihatdan xavf tug'diradi, generatsiya qilinganlari
esa toza va takrorlanadigan. Real suratlar kerak bo'lsa admin panel
orqali almashtiriladi.
"""

import io
import random
from datetime import timedelta
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import ShopProfile, User
from apps.catalog.models import Brand, Category, District, Region
from apps.mediafiles.models import ProductImage
from apps.notifications.models import NotificationPreference
from apps.products.models import Condition, Currency, Product, ProductStatus
from apps.products.services import build_seo_metadata, update_search_vector
from apps.rbac.constants import R
from apps.rbac.models import Role, UserRole

FIRST_NAMES = [
    "Akobir", "Jasur", "Dilshod", "Sardor", "Bekzod", "Aziz", "Shohrux",
    "Otabek", "Javohir", "Ulug'bek", "Nodir", "Farrux", "Sanjar", "Alisher",
    "Madina", "Nilufar", "Sevara", "Kamola", "Dilnoza", "Zilola",
]
LAST_NAMES = [
    "Karimov", "Rahimov", "Yusupov", "Tursunov", "Ergashev", "Sobirov",
    "Nazarov", "Xolmatov", "Qodirov", "Ibragimov", "Mirzayev", "Salimov",
]
SHOP_NAMES = [
    "TechnoMarket", "PC Zone", "Digital Store", "CompStar", "IT Market",
    "Gadget Hub", "Laptop Center", "Komputer Olami", "ProTech", "MegaPC",
]

# Kategoriya slug -> (mahsulot namunalari, narx oralig'i UZS)
CATALOG = {
    "gaming-noutbuklar": (
        [
            ("ASUS", "ROG Strix G16 G614JI", {"cpu": "Intel Core i7-13650HX", "ram_gb": 16, "storage_gb": 1000, "gpu": "RTX 4060", "screen_inch": 16, "refresh_hz": 165, "resolution": "1920x1080", "os": "win11", "storage_type": "ssd_nvme"}),
            ("Lenovo", "Legion 5 Pro", {"cpu": "AMD Ryzen 7 7840HS", "ram_gb": 32, "storage_gb": 1000, "gpu": "RTX 4070", "screen_inch": 16, "refresh_hz": 240, "resolution": "2560x1600", "os": "win11", "storage_type": "ssd_nvme"}),
            ("MSI", "Katana 15 B13V", {"cpu": "Intel Core i7-13620H", "ram_gb": 16, "storage_gb": 512, "gpu": "RTX 4050", "screen_inch": 15.6, "refresh_hz": 144, "resolution": "1920x1080", "os": "dos", "storage_type": "ssd_nvme"}),
            ("Acer", "Nitro V 15", {"cpu": "Intel Core i5-13420H", "ram_gb": 16, "storage_gb": 512, "gpu": "RTX 3050", "screen_inch": 15.6, "refresh_hz": 144, "resolution": "1920x1080", "os": "win11", "storage_type": "ssd_nvme"}),
            ("HP", "Victus 16", {"cpu": "AMD Ryzen 5 7640HS", "ram_gb": 16, "storage_gb": 512, "gpu": "RTX 4060", "screen_inch": 16.1, "refresh_hz": 144, "resolution": "1920x1080", "os": "win11", "storage_type": "ssd_nvme"}),
        ],
        (9_000_000, 28_000_000),
    ),
    "ultrabuklar": (
        [
            ("Apple", "MacBook Air M2 13", {"cpu": "Apple M2", "ram_gb": 8, "storage_gb": 256, "screen_inch": 13.6, "resolution": "2560x1600", "os": "macos", "storage_type": "ssd_nvme"}),
            ("ASUS", "Zenbook 14 OLED", {"cpu": "Intel Core Ultra 7 155H", "ram_gb": 16, "storage_gb": 1000, "screen_inch": 14, "resolution": "2560x1440", "os": "win11", "storage_type": "ssd_nvme"}),
            ("Lenovo", "ThinkPad X1 Carbon Gen 11", {"cpu": "Intel Core i7-1355U", "ram_gb": 16, "storage_gb": 512, "screen_inch": 14, "resolution": "1920x1080", "os": "win11", "storage_type": "ssd_nvme"}),
            ("Dell", "XPS 13 9340", {"cpu": "Intel Core Ultra 7 155H", "ram_gb": 16, "storage_gb": 512, "screen_inch": 13.4, "resolution": "1920x1080", "os": "win11", "storage_type": "ssd_nvme"}),
        ],
        (8_000_000, 26_000_000),
    ),
    "byudjet-noutbuklar": (
        [
            ("HP", "250 G9", {"cpu": "Intel Core i3-1215U", "ram_gb": 8, "storage_gb": 256, "screen_inch": 15.6, "resolution": "1920x1080", "os": "dos", "storage_type": "ssd_nvme"}),
            ("Lenovo", "IdeaPad 3 15", {"cpu": "AMD Ryzen 5 5500U", "ram_gb": 8, "storage_gb": 512, "screen_inch": 15.6, "resolution": "1920x1080", "os": "win11", "storage_type": "ssd_nvme"}),
            ("Acer", "Aspire 3 A315", {"cpu": "Intel Core i5-1235U", "ram_gb": 8, "storage_gb": 512, "screen_inch": 15.6, "resolution": "1920x1080", "os": "dos", "storage_type": "ssd_nvme"}),
        ],
        (3_500_000, 8_500_000),
    ),
    "nvidia-geforce": (
        [
            ("Gigabyte", "RTX 4060 Ti Eagle 8G", {"vram_gb": 8, "memory_type": "gddr6", "memory_bus": 128, "tdp_watt": 160, "interface": "pcie4", "length_mm": 272}),
            ("MSI", "RTX 4070 Super Ventus 3X", {"vram_gb": 12, "memory_type": "gddr6x", "memory_bus": 192, "tdp_watt": 220, "interface": "pcie4", "length_mm": 308}),
            ("ASUS", "TUF RTX 4080 Super", {"vram_gb": 16, "memory_type": "gddr6x", "memory_bus": 256, "tdp_watt": 320, "interface": "pcie4", "length_mm": 348}),
            ("Palit", "RTX 3060 Dual 12G", {"vram_gb": 12, "memory_type": "gddr6", "memory_bus": 192, "tdp_watt": 170, "interface": "pcie4", "length_mm": 245}),
            ("Zotac", "RTX 4060 Twin Edge", {"vram_gb": 8, "memory_type": "gddr6", "memory_bus": 128, "tdp_watt": 115, "interface": "pcie4", "length_mm": 224}),
        ],
        (3_000_000, 22_000_000),
    ),
    "amd-radeon": (
        [
            ("Sapphire", "RX 7800 XT Pulse", {"vram_gb": 16, "memory_type": "gddr6", "memory_bus": 256, "tdp_watt": 263, "interface": "pcie4", "length_mm": 280}),
            ("Gigabyte", "RX 7600 Gaming OC", {"vram_gb": 8, "memory_type": "gddr6", "memory_bus": 128, "tdp_watt": 165, "interface": "pcie4", "length_mm": 282}),
        ],
        (3_500_000, 14_000_000),
    ),
    "intel-cpu": (
        [
            ("Intel", "Core i5-13400F", {"socket": "LGA1700", "cores": 10, "threads": 16, "base_ghz": 2.5, "boost_ghz": 4.6, "tdp_watt": 65, "integrated_gpu": False}),
            ("Intel", "Core i7-13700K", {"socket": "LGA1700", "cores": 16, "threads": 24, "base_ghz": 3.4, "boost_ghz": 5.4, "tdp_watt": 125, "integrated_gpu": True}),
            ("Intel", "Core i9-14900K", {"socket": "LGA1700", "cores": 24, "threads": 32, "base_ghz": 3.2, "boost_ghz": 6.0, "tdp_watt": 125, "integrated_gpu": True}),
        ],
        (2_000_000, 9_500_000),
    ),
    "amd-cpu": (
        [
            ("AMD", "Ryzen 5 7600X", {"socket": "AM5", "cores": 6, "threads": 12, "base_ghz": 4.7, "boost_ghz": 5.3, "tdp_watt": 105, "integrated_gpu": True}),
            ("AMD", "Ryzen 7 7800X3D", {"socket": "AM5", "cores": 8, "threads": 16, "base_ghz": 4.2, "boost_ghz": 5.0, "tdp_watt": 120, "integrated_gpu": True}),
            ("AMD", "Ryzen 9 7950X", {"socket": "AM5", "cores": 16, "threads": 32, "base_ghz": 4.5, "boost_ghz": 5.7, "tdp_watt": 170, "integrated_gpu": True}),
        ],
        (2_500_000, 11_000_000),
    ),
    "gaming-monitorlar": (
        [
            ("Samsung", "Odyssey G5 27", {"screen_inch": 27, "resolution": "2560x1440", "refresh_hz": 165, "panel_type": "va", "response_ms": 1, "curved": True}),
            ("LG", "UltraGear 27GP850", {"screen_inch": 27, "resolution": "2560x1440", "refresh_hz": 180, "panel_type": "ips", "response_ms": 1, "curved": False}),
            ("MSI", "G274F", {"screen_inch": 27, "resolution": "1920x1080", "refresh_hz": 180, "panel_type": "ips", "response_ms": 1, "curved": False}),
            ("Gigabyte", "M32U", {"screen_inch": 32, "resolution": "3840x2160", "refresh_hz": 144, "panel_type": "ips", "response_ms": 1, "curved": False}),
        ],
        (2_200_000, 12_000_000),
    ),
    "ofis-monitorlar": (
        [
            ("Dell", "P2422H", {"screen_inch": 24, "resolution": "1920x1080", "refresh_hz": 60, "panel_type": "ips", "response_ms": 5, "curved": False}),
            ("HP", "M24f", {"screen_inch": 24, "resolution": "1920x1080", "refresh_hz": 75, "panel_type": "ips", "response_ms": 5, "curved": False}),
        ],
        (1_400_000, 3_800_000),
    ),
    "ddr5": (
        [
            ("Kingston", "Fury Beast 32GB (2x16) 6000", {"capacity_gb": 32, "memory_type": "ddr5", "speed_mhz": 6000, "modules": 2, "form_factor": "dimm"}),
            ("Corsair", "Vengeance 32GB (2x16) 5600", {"capacity_gb": 32, "memory_type": "ddr5", "speed_mhz": 5600, "modules": 2, "form_factor": "dimm"}),
            ("ADATA", "XPG Lancer 16GB 5200", {"capacity_gb": 16, "memory_type": "ddr5", "speed_mhz": 5200, "modules": 1, "form_factor": "dimm"}),
        ],
        (900_000, 3_600_000),
    ),
    "ddr4": (
        [
            ("Kingston", "Fury Beast 16GB (2x8) 3200", {"capacity_gb": 16, "memory_type": "ddr4", "speed_mhz": 3200, "modules": 2, "form_factor": "dimm"}),
            ("Patriot", "Viper Steel 32GB (2x16) 3600", {"capacity_gb": 32, "memory_type": "ddr4", "speed_mhz": 3600, "modules": 2, "form_factor": "dimm"}),
        ],
        (600_000, 2_400_000),
    ),
    "ssd-nvme": (
        [
            ("Samsung", "980 PRO 1TB", {"capacity_gb": 1000, "drive_type": "ssd_nvme", "interface": "nvme_pcie4", "read_speed": 7000, "write_speed": 5000}),
            ("Kingston", "NV2 500GB", {"capacity_gb": 500, "drive_type": "ssd_nvme", "interface": "nvme_pcie4", "read_speed": 3500, "write_speed": 2100}),
            ("Crucial", "P3 Plus 2TB", {"capacity_gb": 2000, "drive_type": "ssd_nvme", "interface": "nvme_pcie4", "read_speed": 5000, "write_speed": 4200}),
            ("Western Digital", "SN770 1TB", {"capacity_gb": 1000, "drive_type": "ssd_nvme", "interface": "nvme_pcie4", "read_speed": 5150, "write_speed": 4900}),
        ],
        (500_000, 3_200_000),
    ),
    "hdd": (
        [
            ("Seagate", "Barracuda 2TB", {"capacity_gb": 2000, "drive_type": "hdd", "interface": "sata3", "read_speed": 220}),
            ("Western Digital", "Blue 4TB", {"capacity_gb": 4000, "drive_type": "hdd", "interface": "sata3", "read_speed": 180}),
        ],
        (700_000, 2_000_000),
    ),
    "intel-platform": (
        [
            ("ASUS", "PRIME B760M-K", {"socket": "LGA1700", "chipset": "B760", "form_factor": "micro_atx", "memory_type": "ddr4", "memory_slots": 2, "m2_slots": 1}),
            ("MSI", "MAG B760 Tomahawk", {"socket": "LGA1700", "chipset": "B760", "form_factor": "atx", "memory_type": "ddr5", "memory_slots": 4, "m2_slots": 3}),
            ("Gigabyte", "Z790 AORUS Elite", {"socket": "LGA1700", "chipset": "Z790", "form_factor": "atx", "memory_type": "ddr5", "memory_slots": 4, "m2_slots": 4}),
        ],
        (1_300_000, 5_500_000),
    ),
    "amd-platform": (
        [
            ("ASRock", "B650M PG Riptide", {"socket": "AM5", "chipset": "B650", "form_factor": "micro_atx", "memory_type": "ddr5", "memory_slots": 4, "m2_slots": 2}),
            ("ASUS", "TUF GAMING X670E-PLUS", {"socket": "AM5", "chipset": "X670E", "form_factor": "atx", "memory_type": "ddr5", "memory_slots": 4, "m2_slots": 4}),
        ],
        (1_800_000, 6_500_000),
    ),
    "quvvat-bloklari": (
        [
            ("Corsair", "RM750e 750W", {"wattage": 750, "certification": "80_gold", "modular": "full"}),
            ("be quiet!", "System Power 10 650W", {"wattage": 650, "certification": "80_bronze", "modular": "none"}),
            ("Cooler Master", "MWE 850 V2", {"wattage": 850, "certification": "80_gold", "modular": "full"}),
        ],
        (600_000, 2_400_000),
    ),
    "mexanik-klaviatura": (
        [
            ("Logitech", "G Pro X TKL", {"switch_type": "GX Brown", "layout": "tkl", "connection": "wireless", "backlight": "rgb"}),
            ("Razer", "BlackWidow V4", {"switch_type": "Razer Green", "layout": "full", "connection": "wired", "backlight": "rgb"}),
            ("HyperX", "Alloy Origins Core", {"switch_type": "HyperX Red", "layout": "tkl", "connection": "wired", "backlight": "rgb"}),
        ],
        (450_000, 2_600_000),
    ),
    "gaming-sichqoncha": (
        [
            ("Logitech", "G502 X", {"dpi": 25600, "connection": "wired", "buttons": 13, "weight_g": 89}),
            ("Razer", "DeathAdder V3", {"dpi": 30000, "connection": "wired", "buttons": 6, "weight_g": 59}),
            ("SteelSeries", "Rival 3", {"dpi": 8500, "connection": "wired", "buttons": 6, "weight_g": 77}),
        ],
        (250_000, 1_800_000),
    ),
    "gaming-quloqchin": (
        [
            ("HyperX", "Cloud II", {"connection": "usb", "has_mic": True, "surround": True, "noise_cancelling": False}),
            ("Logitech", "G335", {"connection": "wired_35", "has_mic": True, "surround": False, "noise_cancelling": False}),
        ],
        (400_000, 2_200_000),
    ),
    "lazerli-printer": (
        [
            ("Canon", "i-SENSYS LBP6030", {"print_type": "laser", "color": False, "functions": "Faqat chop etish", "connection": "USB"}),
            ("HP", "LaserJet M211d", {"print_type": "laser", "color": False, "functions": "Chop etish, 2 tomonlama", "connection": "USB"}),
            ("Brother", "DCP-B7530DN", {"print_type": "laser", "color": False, "functions": "Chop, skan, nusxa", "connection": "USB, LAN"}),
        ],
        (1_400_000, 5_000_000),
    ),
    "routerlar": (
        [
            ("TP-Link", "Archer AX53", {"speed_mbps": 3000, "wifi_standard": "wifi6", "ports": 4}),
            ("Mikrotik", "hAP ax lite", {"speed_mbps": 1200, "wifi_standard": "wifi6", "ports": 4}),
        ],
        (450_000, 2_000_000),
    ),
}

CONDITION_WEIGHTS = [
    (Condition.NEW, 30),
    (Condition.LIKE_NEW, 25),
    (Condition.GOOD, 28),
    (Condition.FAIR, 13),
    (Condition.FOR_PARTS, 4),
]

STATUS_WEIGHTS = [
    (ProductStatus.APPROVED, 74),
    (ProductStatus.SOLD, 10),
    (ProductStatus.PENDING, 8),
    (ProductStatus.DRAFT, 4),
    (ProductStatus.REJECTED, 2),
    (ProductStatus.RESERVED, 2),
]

USED_NOTES = [
    "Uy sharoitida ehtiyotkorlik bilan ishlatilgan.",
    "Ish uchun olingan edi, ehtiyojim qolmadi.",
    "Chizilgan joyi yo'q, hujjatlari saqlangan.",
    "Kichik chizilgan joyi bor, ishlashiga ta'siri yo'q.",
    "Servisda tozalangan, termopasta yangilangan.",
]

PALETTE = [
    ("#0f172a", "#334155"), ("#1e1b4b", "#4338ca"), ("#082f49", "#0369a1"),
    ("#1c1917", "#57534e"), ("#052e16", "#15803d"), ("#3b0764", "#7e22ce"),
    ("#450a0a", "#b91c1c"), ("#422006", "#a16207"),
]


class Command(BaseCommand):
    help = "Demo sotuvchilar va mahsulotlarni yaratadi."

    def add_arguments(self, parser):
        parser.add_argument("--products", type=int, default=120)
        parser.add_argument("--sellers", type=int, default=20)
        parser.add_argument("--buyers", type=int, default=20)
        parser.add_argument(
            "--fresh", action="store_true", help="Avvalgi demo ma'lumotni o'chiradi"
        )
        parser.add_argument("--seed", type=int, default=20260921)

    @transaction.atomic
    def handle(self, *args, **options):
        random.seed(options["seed"])

        if options["fresh"]:
            self._wipe()

        if not Category.objects.exists():
            self.stderr.write("Avval `manage.py seed_catalog` ni bajaring.")
            return

        sellers = self._create_users(options["sellers"], is_seller=True)
        self._create_users(options["buyers"], is_seller=False)
        created = self._create_products(options["products"], sellers)

        # Ommaviy yaratishdan keyin hisoblagichlarni bir marta tiklaymiz:
        # har mahsulot uchun alohida sanash 120 marta daraxt bo'ylab
        # yurishni anglatardi.
        call_command("recount")

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo tayyor: {len(sellers)} sotuvchi, {options['buyers']} xaridor, "
                f"{created} mahsulot, {ProductImage.objects.count()} rasm"
            )
        )
        for status_value, label in ProductStatus.choices:
            count = Product.all_objects.filter(status=status_value).count()
            if count:
                self.stdout.write(f"  {label:18} {count}")

    # ------------------------------------------------------------------
    def _wipe(self):
        demo = User.all_objects.filter(phone__startswith="+99890900")
        count = Product.all_objects.filter(seller__in=demo).count()
        Product.all_objects.filter(seller__in=demo).delete()
        demo.delete()
        self.stdout.write(self.style.WARNING(f"Eski demo o'chirildi: {count} mahsulot"))

    def _create_users(self, count, is_seller):
        role = Role.objects.get(code=R.USER)
        regions = list(Region.objects.all())
        users = []

        for index in range(count):
            # Demo raqamlar +99890900xxxx — real raqamlar bilan to'qnashmaydi.
            offset = index if is_seller else 500 + index
            phone = f"+9989090{offset:05d}"
            region = random.choice(regions)

            user, created = User.all_objects.get_or_create(
                phone=phone,
                defaults={
                    "first_name": random.choice(FIRST_NAMES),
                    "last_name": random.choice(LAST_NAMES),
                    "is_active": True,
                    "is_phone_verified": True,
                    "region": region,
                    "is_verified_seller": is_seller and random.random() < 0.3,
                },
            )
            if created:
                user.set_password("Demo#Parol2026")
                user.save()
                UserRole.objects.get_or_create(user=user, role=role)
                NotificationPreference.objects.get_or_create(user=user)

                districts = list(region.districts.all())
                if districts:
                    user.district = random.choice(districts)
                    user.save(update_fields=["district"])

                # Sotuvchilarning uchdan biri do'kon sifatida ishlaydi.
                if is_seller and random.random() < 0.35:
                    ShopProfile.objects.get_or_create(
                        user=user,
                        defaults={
                            "name": f"{random.choice(SHOP_NAMES)} {random.randint(1, 99)}",
                            "description": "Kompyuter texnikasi va komplektuvchilari.",
                            "working_hours": "Du-Sha 10:00-19:00",
                        },
                    )
            users.append(user)
        return users

    # ------------------------------------------------------------------
    def _create_products(self, target, sellers):
        categories = {c.slug: c for c in Category.objects.all()}
        brands = {b.name: b for b in Brand.objects.all()}
        created = 0

        pool = []
        for slug, (items, price_range) in CATALOG.items():
            if slug not in categories:
                continue
            for item in items:
                pool.append((categories[slug], item, price_range))

        if not pool:
            return 0

        while created < target:
            category, (brand_name, model, specs), (low, high) = random.choice(pool)
            seller = random.choice(sellers)
            condition = _weighted(CONDITION_WEIGHTS)
            status = _weighted(STATUS_WEIGHTS)

            # Ishlatilgan mahsulot arzonroq — narx holatga bog'lansin.
            factor = {
                Condition.NEW: 1.0,
                Condition.LIKE_NEW: 0.85,
                Condition.GOOD: 0.72,
                Condition.FAIR: 0.55,
                Condition.FOR_PARTS: 0.3,
            }[condition]
            price = Decimal(int(random.randint(low, high) * factor / 10_000) * 10_000)

            is_used = condition != Condition.NEW
            title = f"{brand_name} {model}"
            if is_used:
                title += f" ({dict(Condition.choices)[condition]})"

            description = [
                f"{brand_name} {model} sotiladi.",
                random.choice(USED_NOTES) if is_used else "Yangi, ochilmagan, kafolat bilan.",
                "Savollar bo'lsa qo'ng'iroq qiling yoki Telegram orqali yozing.",
            ]

            created_at = timezone.now() - timedelta(
                days=random.randint(0, 60), hours=random.randint(0, 23)
            )

            product = Product(
                title=title[:200],
                description=" ".join(description),
                seller=seller,
                category=category,
                brand=brands.get(brand_name),
                model_name=model,
                price=price,
                currency=Currency.UZS,
                is_negotiable=random.random() < 0.45,
                is_exchange_possible=random.random() < 0.15,
                condition=condition,
                status=status,
                specs={**specs, "warranty_months": random.choice([0, 3, 6, 12, 24])},
                region=seller.region,
                district=seller.district,
                usage_period=random.choice(["3 oy", "6 oy", "1 yil", "1.5 yil", "2 yil"]) if is_used else "",
                has_warranty=random.random() < 0.4,
                has_original_box=random.random() < 0.5,
                accessories="Original quti, zaryadlovchi" if random.random() < 0.4 else "",
                is_featured=random.random() < 0.08,
                created_by=seller,
                views_count=random.randint(0, 900),
                favorites_count=random.randint(0, 60),
                phone_reveals_count=random.randint(0, 120),
            )
            if product.has_warranty:
                product.warranty_until = (created_at + timedelta(days=random.randint(90, 730))).date()

            if status in (ProductStatus.APPROVED, ProductStatus.SOLD, ProductStatus.RESERVED):
                product.published_at = created_at
                product.bumped_at = created_at
                product.expires_at = created_at + timedelta(days=30)
            if status == ProductStatus.SOLD:
                product.sold_at = created_at + timedelta(days=random.randint(1, 20))

            build_seo_metadata(product)
            product.save()

            # created_at auto_now_add bo'lgani uchun keyin yangilanadi.
            Product.all_objects.filter(pk=product.pk).update(created_at=created_at)

            self._attach_images(product, brand_name, model, random.randint(2, 4))
            update_search_vector(product)
            created += 1

        return created

    # ------------------------------------------------------------------
    def _attach_images(self, product, brand, model, count):
        from PIL import Image, ImageDraw

        dark, light = random.choice(PALETTE)
        for index in range(count):
            image = Image.new("RGB", (1280, 960), dark)
            draw = ImageDraw.Draw(image)

            # Oddiy, lekin katalogda chiroyli ko'rinadigan geometrik naqsh.
            draw.rounded_rectangle([90, 90, 1190, 870], radius=28, outline=light, width=6)
            draw.rounded_rectangle([150, 220, 1130, 740], radius=18, fill=light)
            draw.text((170, 140), f"{brand}".upper(), fill="#f8fafc")
            draw.text((170, 790), f"{model}  ·  {index + 1}/{count}", fill="#cbd5e1")

            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=85)
            buffer.seek(0)

            ProductImage.objects.create(
                product=product,
                image=ContentFile(buffer.read(), name=f"{product.slug}.jpg"),
                alt_text=f"{product.title} - rasm {index + 1}",
                is_primary=index == 0,
                order=index,
                width=1280,
                height=960,
                file_size=buffer.getbuffer().nbytes,
                is_processed=False,
            )


def _weighted(pairs):
    values, weights = zip(*pairs)
    return random.choices(values, weights=weights, k=1)[0]
