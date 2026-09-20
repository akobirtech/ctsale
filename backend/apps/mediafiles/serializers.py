"""Media serializerlari."""

from rest_framework import serializers

from .models import ProductImage, ProductVideo


class ProductImageSerializer(serializers.ModelSerializer):
    """Rasm — barcha o'lchamlari bilan.

    Frontend `srcset` qurishi uchun uchala o'lcham ham beriladi;
    optimizatsiya tugamagan bo'lsa originalga qaytadi.
    """

    url = serializers.SerializerMethodField()
    thumb_url = serializers.SerializerMethodField()
    medium_url = serializers.SerializerMethodField()
    large_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductImage
        fields = [
            "id", "url", "thumb_url", "medium_url", "large_url",
            "alt_text", "is_primary", "order", "width", "height", "is_processed",
        ]
        read_only_fields = ["id", "width", "height", "is_processed"]

    def _absolute(self, file_field):
        if not file_field:
            return None
        url = file_field.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def get_url(self, obj):
        return self._absolute(obj.image)

    def get_thumb_url(self, obj):
        return self._absolute(obj.thumb or obj.medium or obj.image)

    def get_medium_url(self, obj):
        return self._absolute(obj.medium or obj.image)

    def get_large_url(self, obj):
        return self._absolute(obj.large or obj.image)


class ProductVideoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    poster_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductVideo
        fields = [
            "id", "url", "poster_url", "title", "order",
            "duration_seconds", "mime_type", "is_processed",
        ]
        read_only_fields = ["id", "duration_seconds", "mime_type", "is_processed"]

    def _absolute(self, file_field):
        if not file_field:
            return None
        url = file_field.url
        request = self.context.get("request")
        return request.build_absolute_uri(url) if request else url

    def get_url(self, obj):
        return self._absolute(obj.video)

    def get_poster_url(self, obj):
        return self._absolute(obj.poster)


class ImageReorderSerializer(serializers.Serializer):
    """Drag & drop natijasi: [{id, order}, ...]"""

    items = serializers.ListField(
        child=serializers.DictField(), allow_empty=False, max_length=50
    )

    def validate_items(self, value):
        for item in value:
            if "id" not in item or "order" not in item:
                raise serializers.ValidationError(
                    "Har bir element `id` va `order` maydonlariga ega bo'lishi kerak."
                )
        return value
