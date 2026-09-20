"""Moderatsiya serializerlari."""

from rest_framework import serializers

from apps.products.serializers import ProductCardSerializer

from .models import ModerationTask, RejectReasonCode


class ModerationTaskSerializer(serializers.ModelSerializer):
    product = ProductCardSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    reason_display = serializers.CharField(source="get_reason_code_display", read_only=True)
    assignee_name = serializers.SerializerMethodField()
    seller_name = serializers.SerializerMethodField()
    waiting_hours = serializers.SerializerMethodField()

    class Meta:
        model = ModerationTask
        fields = [
            "id", "product", "status", "status_display",
            "reason_code", "reason_display", "comment", "internal_note",
            "assignee", "assignee_name", "seller_name",
            "is_resubmission", "waiting_hours", "created_at", "reviewed_at",
        ]

    def get_assignee_name(self, obj):
        return obj.assignee.get_full_name() if obj.assignee_id else None

    def get_seller_name(self, obj):
        seller = obj.product.seller
        return seller.get_full_name() or seller.phone

    def get_waiting_hours(self, obj):
        """Navbatda qancha turgani — moderator ustuvorlikni ko'rsin."""
        if obj.reviewed_at:
            return None
        from django.utils import timezone

        return round((timezone.now() - obj.created_at).total_seconds() / 3600, 1)


class RejectSerializer(serializers.Serializer):
    reason_code = serializers.ChoiceField(choices=RejectReasonCode.choices)
    comment = serializers.CharField(
        max_length=1000, required=False, allow_blank=True,
        help_text="Sotuvchiga ko'rinadi",
    )
    internal_note = serializers.CharField(
        max_length=1000, required=False, allow_blank=True,
        help_text="Faqat xodimlarga ko'rinadi",
    )

    def validate(self, attrs):
        # "Boshqa sabab" tanlansa izohsiz sotuvchi nima qilishini bilmaydi.
        if attrs["reason_code"] == RejectReasonCode.OTHER and not attrs.get("comment"):
            raise serializers.ValidationError(
                {"comment": "«Boshqa sabab» tanlanganda izoh yozish majburiy."}
            )
        return attrs


class BulkApproveSerializer(serializers.Serializer):
    task_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=False, max_length=50
    )
