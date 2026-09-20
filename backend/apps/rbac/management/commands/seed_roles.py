"""Standart rollar va ruxsatlarni bazaga yozadi (idempotent)."""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.rbac.constants import PERMISSION_CATALOG, ROLE_CATALOG
from apps.rbac.models import Permission, Role, RolePermission


class Command(BaseCommand):
    help = "Standart rollar va ruxsatlarni yaratadi yoki yangilaydi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--prune",
            action="store_true",
            help="Katalogda yo'q ruxsatlarni o'chiradi (ehtiyot bo'ling).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        created_permissions = 0
        for code, (name, group, description) in PERMISSION_CATALOG.items():
            _, created = Permission.objects.update_or_create(
                code=code,
                defaults={"name": name, "group": group, "description": description},
            )
            created_permissions += int(created)

        if options["prune"]:
            removed, _ = Permission.objects.exclude(
                code__in=PERMISSION_CATALOG.keys()
            ).delete()
            if removed:
                self.stdout.write(self.style.WARNING(f"{removed} ta eski ruxsat o'chirildi"))

        all_permissions = {p.code: p for p in Permission.objects.all()}
        created_roles = 0

        for code, spec in ROLE_CATALOG.items():
            role, created = Role.objects.update_or_create(
                code=code,
                defaults={
                    "name": spec["name"],
                    "description": spec["description"],
                    "is_system": spec["is_system"],
                    "is_staff_role": spec["is_staff_role"],
                    "order": spec["order"],
                },
            )
            created_roles += int(created)

            wanted = spec["permissions"]
            codes = set(all_permissions) if wanted == "*" else set(wanted)

            existing = set(
                RolePermission.objects.filter(role=role).values_list(
                    "permission__code", flat=True
                )
            )
            for missing in codes - existing:
                RolePermission.objects.create(
                    role=role, permission=all_permissions[missing]
                )
            # Kataloga mos kelmaydiganlarni olib tashlaymiz, aks holda
            # roldan ruxsat olib tashlash hech qachon kuchga kirmaydi.
            RolePermission.objects.filter(role=role).exclude(
                permission__code__in=codes
            ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f"Ruxsatlar: {Permission.objects.count()} ta (+{created_permissions} yangi), "
                f"rollar: {Role.objects.count()} ta (+{created_roles} yangi)"
            )
        )
        for role in Role.objects.order_by("order"):
            self.stdout.write(f"  {role.code:12} - {role.permissions.count():2} ruxsat")
