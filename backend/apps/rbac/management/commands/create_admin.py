"""Admin hisobini yaratadi yoki mavjudiga rol beradi."""

import getpass

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.core.utils import normalize_phone
from apps.rbac.constants import R
from apps.rbac.models import Role, UserRole


class Command(BaseCommand):
    help = "Admin/superadmin hisobini yaratadi."

    def add_arguments(self, parser):
        parser.add_argument("--phone", required=True, help="+998XXXXXXXXX")
        parser.add_argument("--password", help="Ko'rsatilmasa so'raladi")
        parser.add_argument("--first-name", default="")
        parser.add_argument("--last-name", default="")
        parser.add_argument(
            "--role",
            default=R.SUPERADMIN,
            choices=[R.SUPERADMIN, R.ADMIN, R.MODERATOR, R.SUPPORT],
        )

    @transaction.atomic
    def handle(self, *args, **options):
        phone = normalize_phone(options["phone"])
        password = options.get("password")
        if not password:
            password = getpass.getpass("Parol: ")
            if password != getpass.getpass("Parolni takrorlang: "):
                raise CommandError("Parollar mos kelmadi.")
        if len(password) < 8:
            raise CommandError("Parol kamida 8 ta belgidan iborat bo'lsin.")

        role = Role.objects.filter(code=options["role"]).first()
        if role is None:
            raise CommandError(
                f"'{options['role']}' roli topilmadi. Avval `manage.py seed_roles` ni bajaring."
            )

        user = User.all_objects.filter(phone=phone).first()
        if user is None:
            user = User.objects.create_user(
                phone=phone,
                password=password,
                first_name=options["first_name"],
                last_name=options["last_name"],
            )
            action = "yaratildi"
        else:
            user.set_password(password)
            action = "yangilandi"

        # Admin hisobiga OTP tasdiqlash talab qilinmaydi.
        user.is_active = True
        user.is_phone_verified = True
        user.is_staff = True
        user.is_superuser = options["role"] == R.SUPERADMIN
        user.is_deleted = False
        if options["first_name"]:
            user.first_name = options["first_name"]
        if options["last_name"]:
            user.last_name = options["last_name"]
        user.save()

        UserRole.objects.get_or_create(user=user, role=role)
        UserRole.objects.get_or_create(
            user=user, role=Role.objects.get(code=R.USER)
        )

        from apps.notifications.models import NotificationPreference

        NotificationPreference.objects.get_or_create(user=user)

        self.stdout.write(
            self.style.SUCCESS(
                f"Hisob {action}: {phone} | rol: {role.code} | "
                f"ruxsatlar: {len(user.permission_codes())} ta"
            )
        )
