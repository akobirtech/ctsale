"""Ruxsat kodlari va standart rollar.

Bu yagona manba: yangi ruxsat qo'shish uchun shu yerga qator qo'shiladi
va `manage.py seed_roles` ishga tushiriladi. Kodda esa doim
`P.PRODUCT_APPROVE` kabi konstanta ishlatiladi — matn xatolari
kompilyatsiya paytida emas, lekin IDE'da darhol ko'rinadi.
"""


class P:
    """Permission kodlari."""

    # --- Mahsulot ---
    PRODUCT_VIEW_ANY = "product.view_any"
    PRODUCT_EDIT_ANY = "product.edit_any"
    PRODUCT_DELETE_ANY = "product.delete_any"
    PRODUCT_APPROVE = "product.approve"
    PRODUCT_REJECT = "product.reject"
    PRODUCT_FEATURE = "product.feature"
    PRODUCT_FORCE_STATUS = "product.force_status"

    # --- Foydalanuvchi ---
    USER_VIEW = "user.view"
    USER_EDIT = "user.edit"
    USER_BAN = "user.ban"
    USER_CHANGE_ROLE = "user.change_role"
    USER_VERIFY_SELLER = "user.verify_seller"

    # --- Katalog ---
    CATEGORY_MANAGE = "category.manage"
    BRAND_MANAGE = "brand.manage"
    ATTRIBUTE_MANAGE = "attribute.manage"
    LOCATION_MANAGE = "location.manage"

    # --- Telegram ---
    TELEGRAM_MANAGE = "telegram.manage"
    TELEGRAM_PUBLISH = "telegram.publish"

    # --- Shikoyatlar ---
    REPORT_VIEW = "report.view"
    REPORT_RESOLVE = "report.resolve"

    # --- Tizim ---
    AUDIT_VIEW = "audit.view"
    STATS_VIEW = "stats.view"
    SEO_MANAGE = "seo.manage"
    ROLE_MANAGE = "role.manage"
    SETTINGS_MANAGE = "settings.manage"


# code -> (nomi, guruh, izoh)
PERMISSION_CATALOG = {
    P.PRODUCT_VIEW_ANY: ("Barcha e'lonlarni ko'rish", "product", "Qoralama va rad etilganlar ham"),
    P.PRODUCT_EDIT_ANY: ("Istalgan e'lonni tahrirlash", "product", ""),
    P.PRODUCT_DELETE_ANY: ("Istalgan e'lonni o'chirish", "product", ""),
    P.PRODUCT_APPROVE: ("E'lonni tasdiqlash", "moderation", "Telegram postini ishga tushiradi"),
    P.PRODUCT_REJECT: ("E'lonni rad etish", "moderation", "Sabab ko'rsatish majburiy"),
    P.PRODUCT_FEATURE: ("E'lonni VIP qilish", "product", ""),
    P.PRODUCT_FORCE_STATUS: ("Statusni majburan o'zgartirish", "product", "Holat mashinasini chetlab o'tadi"),
    P.USER_VIEW: ("Foydalanuvchilarni ko'rish", "user", ""),
    P.USER_EDIT: ("Foydalanuvchini tahrirlash", "user", ""),
    P.USER_BAN: ("Foydalanuvchini bloklash", "user", ""),
    P.USER_CHANGE_ROLE: ("Rolni o'zgartirish", "user", ""),
    P.USER_VERIFY_SELLER: ("Sotuvchini tasdiqlash", "user", "Ko'k belgi beradi"),
    P.CATEGORY_MANAGE: ("Kategoriyalarni boshqarish", "catalog", ""),
    P.BRAND_MANAGE: ("Brendlarni boshqarish", "catalog", ""),
    P.ATTRIBUTE_MANAGE: ("Xususiyatlarni boshqarish", "catalog", ""),
    P.LOCATION_MANAGE: ("Hududlarni boshqarish", "catalog", ""),
    P.TELEGRAM_MANAGE: ("Telegram sozlamalari", "telegram", ""),
    P.TELEGRAM_PUBLISH: ("Telegramga qo'lda joylash", "telegram", ""),
    P.REPORT_VIEW: ("Shikoyatlarni ko'rish", "report", ""),
    P.REPORT_RESOLVE: ("Shikoyat bo'yicha qaror", "report", ""),
    P.AUDIT_VIEW: ("Audit jurnalini ko'rish", "system", ""),
    P.STATS_VIEW: ("Statistikani ko'rish", "system", ""),
    P.SEO_MANAGE: ("SEO sozlamalari", "system", ""),
    P.ROLE_MANAGE: ("Rollarni boshqarish", "system", "Ehtiyot bo'ling: ruxsat berish huquqi"),
    P.SETTINGS_MANAGE: ("Tizim sozlamalari", "system", ""),
}


class R:
    """Rol kodlari."""

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPPORT = "support"
    USER = "user"


# Har bir standart rolga biriktiriladigan ruxsatlar.
# SUPERADMIN ro'yxatga muhtoj emas — u har doim hamma narsaga ega.
ROLE_CATALOG = {
    R.SUPERADMIN: {
        "name": "Bosh administrator",
        "description": "Cheklovsiz kirish. Rollar va tizim sozlamalari.",
        "is_system": True,
        "is_staff_role": True,
        "order": 0,
        "permissions": "*",
    },
    R.ADMIN: {
        "name": "Administrator",
        "description": "Kundalik boshqaruv: katalog, e'lonlar, Telegram, statistika.",
        "is_system": True,
        "is_staff_role": True,
        "order": 1,
        "permissions": [
            P.PRODUCT_VIEW_ANY, P.PRODUCT_EDIT_ANY, P.PRODUCT_DELETE_ANY,
            P.PRODUCT_APPROVE, P.PRODUCT_REJECT, P.PRODUCT_FEATURE,
            P.USER_VIEW, P.USER_EDIT, P.USER_BAN, P.USER_VERIFY_SELLER,
            P.CATEGORY_MANAGE, P.BRAND_MANAGE, P.ATTRIBUTE_MANAGE, P.LOCATION_MANAGE,
            P.TELEGRAM_MANAGE, P.TELEGRAM_PUBLISH,
            P.REPORT_VIEW, P.REPORT_RESOLVE,
            P.AUDIT_VIEW, P.STATS_VIEW, P.SEO_MANAGE,
        ],
    },
    R.MODERATOR: {
        "name": "Moderator",
        "description": "E'lonlarni tasdiqlash/rad etish va shikoyatlar.",
        "is_system": True,
        "is_staff_role": True,
        "order": 2,
        "permissions": [
            P.PRODUCT_VIEW_ANY, P.PRODUCT_APPROVE, P.PRODUCT_REJECT,
            P.REPORT_VIEW, P.REPORT_RESOLVE, P.STATS_VIEW,
        ],
    },
    R.SUPPORT: {
        "name": "Qo'llab-quvvatlash",
        "description": "Foydalanuvchilar bilan ishlash, shikoyatlarni ko'rish.",
        "is_system": True,
        "is_staff_role": True,
        "order": 3,
        "permissions": [P.USER_VIEW, P.PRODUCT_VIEW_ANY, P.REPORT_VIEW],
    },
    R.USER: {
        "name": "Foydalanuvchi",
        "description": "Oddiy foydalanuvchi — o'z e'lonlarini boshqaradi.",
        "is_system": True,
        "is_staff_role": False,
        "order": 9,
        "permissions": [],
    },
}
