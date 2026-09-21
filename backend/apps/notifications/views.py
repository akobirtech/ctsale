"""Bildirishnomalar."""

from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification, NotificationPreference
from .serializers import NotificationPreferenceSerializer, NotificationSerializer
from .services import mark_all_read


class NotificationViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by("-created_at")

    def list(self, request):
        queryset = self.get_queryset()
        if request.query_params.get("unread") == "true":
            queryset = queryset.filter(is_read=False)

        page = self.paginate_queryset(queryset)
        response = self.get_paginated_response(
            NotificationSerializer(page, many=True).data
        )
        response.data["unread_count"] = self.get_queryset().filter(is_read=False).count()
        return response

    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request):
        """Qo'ng'iroqcha belgisi uchun — eng tez-tez chaqiriladigan endpoint."""
        return Response({"count": self.get_queryset().filter(is_read=False).count()})

    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request, pk=None):
        notification = self.get_queryset().filter(pk=pk).first()
        if notification is None:
            return Response({"detail": "Topilmadi."}, status=404)
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = timezone.now()
            notification.save(update_fields=["is_read", "read_at"])
        return Response({"detail": "O'qilgan deb belgilandi."})

    @action(detail=False, methods=["post"], url_path="read-all")
    def mark_all(self, request):
        count = mark_all_read(request.user)
        return Response({"detail": f"{count} ta bildirishnoma o'qilgan deb belgilandi."})

    @action(detail=False, methods=["get", "patch"])
    def preferences(self, request):
        preference, _ = NotificationPreference.objects.get_or_create(user=request.user)

        if request.method == "PATCH":
            serializer = NotificationPreferenceSerializer(
                preference, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        return Response(NotificationPreferenceSerializer(preference).data)
