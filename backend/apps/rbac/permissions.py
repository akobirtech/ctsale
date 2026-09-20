"""DRF permission classlari.

Ikki bosqichli tekshiruv:
  1. Harakat darajasi — foydalanuvchida kerakli permission kodi bormi?
  2. Obyekt darajasi — bu aynan uning obyektimi?

Ikkalasi ham kerak: `product.edit_any` bo'lmagan foydalanuvchi faqat
o'z e'lonini tahrirlay oladi.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from .constants import P


def user_has_permission(user, code):
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "ban_is_active", False):
        return False
    return user.has_perm_code(code)


class HasPermission(BasePermission):
    """Ko'rinish `required_permission` atributini e'lon qiladi.

        class ProductApproveView(APIView):
            permission_classes = [HasPermission]
            required_permission = P.PRODUCT_APPROVE
    """

    message = "Sizda bu amalni bajarish uchun ruxsat yo'q."

    def has_permission(self, request, view):
        code = getattr(view, "required_permission", None)
        if code is None:
            # Ruxsat kodi ko'rsatilmagan bo'lsa ochib qo'yishdan ko'ra
            # yopib qo'ygan xavfsizroq.
            return False
        return user_has_permission(request.user, code)


def require(code):
    """Bitta ruxsat uchun tayyor class yasaydi.

        permission_classes = [require(P.PRODUCT_APPROVE)]
    """

    class _Required(BasePermission):
        message = "Sizda bu amalni bajarish uchun ruxsat yo'q."

        def has_permission(self, request, view):
            return user_has_permission(request.user, code)

    _Required.__name__ = f"Require_{code.replace('.', '_')}"
    return _Required


def require_any(*codes):
    """Sanab o'tilgan ruxsatlardan kamida bittasi yetarli."""

    class _RequiredAny(BasePermission):
        message = "Sizda bu amalni bajarish uchun ruxsat yo'q."

        def has_permission(self, request, view):
            return any(user_has_permission(request.user, code) for code in codes)

    return _RequiredAny


class IsStaff(BasePermission):
    """Admin panelga kirish: xodim roli yoki superuser."""

    message = "Bu bo'lim faqat xodimlar uchun."

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or user.ban_is_active:
            return False
        if user.is_superuser or user.is_staff:
            return True
        return user.roles.filter(role__is_staff_role=True).exists()


class IsOwnerOrReadOnly(BasePermission):
    """O'qish hammaga, o'zgartirish faqat egasiga (yoki ruxsati borga)."""

    owner_field = "seller"
    message = "Bu obyektni faqat egasi o'zgartira oladi."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if user_has_permission(request.user, P.PRODUCT_EDIT_ANY):
            return True
        owner_field = getattr(view, "owner_field", self.owner_field)
        owner_id = getattr(obj, f"{owner_field}_id", None)
        return bool(owner_id) and owner_id == request.user.id


class IsOwner(BasePermission):
    """Faqat egasi — o'qish uchun ham."""

    owner_field = "user"
    message = "Bu ma'lumot sizga tegishli emas."

    def has_object_permission(self, request, view, obj):
        owner_field = getattr(view, "owner_field", self.owner_field)
        owner_id = getattr(obj, f"{owner_field}_id", None)
        return bool(owner_id) and owner_id == request.user.id


class IsNotBanned(BasePermission):
    """Bloklangan foydalanuvchi o'qiy oladi, lekin yoza olmaydi."""

    message = "Hisobingiz bloklangan. Qo'llab-quvvatlash xizmatiga murojaat qiling."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return not (user and user.is_authenticated and user.ban_is_active)


class IsPhoneVerified(BasePermission):
    """E'lon joylash uchun telefon tasdiqlangan bo'lishi shart."""

    message = "E'lon joylash uchun telefon raqamingizni tasdiqlang."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.is_phone_verified)
