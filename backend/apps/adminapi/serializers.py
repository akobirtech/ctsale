"""Admin panel serializerlari."""

from rest_framework import serializers

from apps.accounts.models import User
from apps.analytics.models import AuditLog
from apps.products.models import Product
from apps.telegrambot.models import TelegramPost, TelegramSettings


class AdminUserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name", read_only=True)
    roles = serializers.SerializerMethodField()
    products_total = serializers.IntegerField(read_only=True, default=0)
    region_name = serializers.CharField(source="region.name_uz", read_only=True, default=None)
    ban_is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "phone", "email", "first_name", "last_name", "full_name",
            "avatar", "region_name", "roles", "products_total",
            "is_active", "is_staff", "is_superuser",
            "is_phone_verified", "is_verified_seller",
            "is_banned", "ban_is_active", "ban_reason", "banned_until",
            "created_at", "last_seen_at",
        ]
        read_only_fields = fields

    def get_roles(self, obj):
        return [item.role.code for item in obj.roles.all()]


class AuditLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source="get_action_display", read_only=True)
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            "id", "actor", "actor_name", "actor_label",
            "action", "action_display",
            "target_type", "target_id", "target_label",
            "changes", "note", "ip_address", "created_at",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj):
        if obj.actor_id:
            return obj.actor.get_full_name() or obj.actor.phone
        return obj.actor_label or "tizim"


class TelegramPostSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    product_title = serializers.CharField(source="product.title", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    message_url = serializers.CharField(read_only=True)

    class Meta:
        model = TelegramPost
        fields = [
            "id", "product", "product_title", "product_slug",
            "status", "status_display", "method", "channel_id",
            "message_id", "message_url", "rendered_text",
            "error_message", "retry_count", "is_mock",
            "published_at", "created_at",
        ]
        read_only_fields = fields


class TelegramSettingsSerializer(serializers.ModelSerializer):
    """Telegram sozlamalari.

    Bot tokeni bu yerda YO'Q — u faqat `.env` da yashaydi va hech
    qachon API javobiga chiqmaydi.
    """

    class Meta:
        model = TelegramSettings
        fields = [
            "channel_id", "channel_url", "auto_publish",
            "publish_media", "publish_video", "update_on_sold",
            "post_template", "sold_suffix", "button_text",
            "max_specs_in_post", "is_enabled", "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate_post_template(self, value):
        # Shablon noma'lum o'zgaruvchi bilan saqlansa postlar buziladi —
        # saqlashdan oldin sinab ko'ramiz.
        allowed = {
            "title", "price", "condition", "category", "brand", "model",
            "specs_line", "location", "url", "seller", "description",
        }
        try:
            value.format(**{key: "" for key in allowed})
        except KeyError as exc:
            raise serializers.ValidationError(
                f"Noma'lum o'zgaruvchi: {exc}. Mavjudlari: {', '.join(sorted(allowed))}"
            ) from exc
        except (IndexError, ValueError) as exc:
            raise serializers.ValidationError(
                "Shablonda formatlash xatosi bor. Jingalak qavslarni tekshiring."
            ) from exc
        return value


class AdminProductSerializer(serializers.ModelSerializer):
    """Admin jadvali uchun qisqa ko'rinish.

    Ommaviy serializer'dan farqi: qoralama va rad etilgan e'lonlar ham
    ko'rinadi, sotuvchi va moderatsiya holati esa bitta qatorda turadi.
    """

    seller_phone = serializers.CharField(source="seller.phone", read_only=True)
    seller_name = serializers.CharField(source="seller.get_full_name", read_only=True)
    category_name = serializers.CharField(source="category.name_uz", read_only=True)
    cover = serializers.SerializerMethodField()
    telegram_status = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "slug",
            "title",
            "status",
            "price",
            "currency",
            "condition",
            "is_featured",
            "featured_until",
            "views_count",
            "seller_phone",
            "seller_name",
            "category_name",
            "cover",
            "telegram_status",
            "created_at",
            "published_at",
        ]
        read_only_fields = fields

    def get_cover(self, product):
        images = list(product.images.all())
        image = next((i for i in images if i.is_primary), None) or next(iter(images), None)
        return image.thumb_url if image else None

    def get_telegram_status(self, product):
        post = next(iter(product.telegram_posts.all()), None)
        return post.status if post else None
