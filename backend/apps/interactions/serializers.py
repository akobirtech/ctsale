"""Sevimlilar va shikoyatlar serializerlari."""

from rest_framework import serializers

from .models import Favorite, Report, ReportReason


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ["id", "product", "created_at"]
        read_only_fields = ["id", "created_at"]


class ReportSerializer(serializers.Serializer):
    """Foydalanuvchi yuboradigan shikoyat."""

    slug = serializers.CharField(max_length=255)
    reason = serializers.ChoiceField(choices=ReportReason.choices)
    comment = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    def validate(self, attrs):
        # "Boshqa" sababda izohsiz moderator nimani tekshirishini bilmaydi.
        if attrs["reason"] == ReportReason.OTHER and not attrs.get("comment", "").strip():
            raise serializers.ValidationError(
                {"comment": "«Boshqa» sababi tanlanganda izoh yozish majburiy."}
            )
        return attrs


class ReportAdminSerializer(serializers.ModelSerializer):
    """Xodimlar ko'radigan to'liq ko'rinish."""

    reason_display = serializers.CharField(source="get_reason_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    product_title = serializers.CharField(source="product.title", read_only=True)
    product_slug = serializers.CharField(source="product.slug", read_only=True)
    product_status = serializers.CharField(source="product.status", read_only=True)
    reporter_name = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id", "product", "product_title", "product_slug", "product_status",
            "reason", "reason_display", "comment",
            "status", "status_display", "resolution_note",
            "reporter", "reporter_name", "seller_name",
            "resolved_by", "resolved_by_name", "resolved_at", "created_at",
        ]

    def get_reporter_name(self, obj):
        if not obj.reporter_id:
            return "Anonim"
        return obj.reporter.get_full_name() or obj.reporter.phone

    def get_resolved_by_name(self, obj):
        return obj.resolved_by.get_full_name() if obj.resolved_by_id else None

    def get_seller_name(self, obj):
        seller = obj.product.seller
        return seller.get_full_name() or seller.phone
