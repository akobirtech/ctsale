"""Parol validatorlari — o'zbekcha xabarlar bilan.

Django'ning standart validatorlari inglizcha xabar beradi. Tarjima
fayllari o'rniga to'g'ridan-to'g'ri o'zbekcha yozilgan validatorlar
ishlatiladi: xabarlar aniqroq va nima qilish kerakligini aytadi.
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class UzMinimumLengthValidator:
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise ValidationError(
                f"Parol kamida {self.min_length} ta belgidan iborat bo'lishi kerak.",
                code="password_too_short",
            )

    def get_help_text(self):
        return f"Parol kamida {self.min_length} ta belgidan iborat bo'lsin."


class UzCommonPasswordValidator:
    """Eng ko'p ishlatiladigan parollarni rad etadi."""

    COMMON = {
        "password", "parol", "12345678", "123456789", "qwerty123", "qwertyui",
        "11111111", "00000000", "abc12345", "password1", "iloveyou", "admin123",
        "welcome1", "letmein1", "monkey12", "dragon12", "sunshine", "princess",
        "football", "baseball", "superman", "trustno1", "1q2w3e4r", "zaq12wsx",
        "asdfghjk", "87654321", "qazwsxed", "computer", "internet",
    }

    def validate(self, password, user=None):
        if password.lower() in self.COMMON:
            raise ValidationError(
                "Bu parol juda keng tarqalgan. Boshqa parol tanlang.",
                code="password_too_common",
            )

    def get_help_text(self):
        return "Keng tarqalgan parollardan foydalanmang."


class UzNumericPasswordValidator:
    def validate(self, password, user=None):
        if password.isdigit():
            raise ValidationError(
                "Parol faqat raqamlardan iborat bo'lmasligi kerak. "
                "Harf va belgilar qo'shing.",
                code="password_entirely_numeric",
            )

    def get_help_text(self):
        return "Parolda harflar ham bo'lsin."


class UzComplexityValidator:
    """Kamida bitta harf va bitta raqam bo'lishini talab qiladi.

    Maxsus belgi majburiy emas: OWASP tavsiyasiga ko'ra uzunlik
    murakkablik qoidalaridan muhimroq va qattiq qoidalar
    foydalanuvchini oson taxmin qilinadigan naqshlarga majburlaydi.
    """

    def validate(self, password, user=None):
        if not re.search(r"[A-Za-z]", password):
            raise ValidationError(
                "Parolda kamida bitta harf bo'lishi kerak.", code="password_no_letter"
            )
        if not re.search(r"\d", password):
            raise ValidationError(
                "Parolda kamida bitta raqam bo'lishi kerak.", code="password_no_digit"
            )

    def get_help_text(self):
        return "Parolda harf va raqam bo'lsin."


class UzUserAttributeSimilarityValidator:
    """Parol telefon raqam yoki ismga o'xshash bo'lmasin."""

    ATTRIBUTES = ("phone", "first_name", "last_name", "email")

    def validate(self, password, user=None):
        if user is None:
            return
        lowered = password.lower()
        for attribute in self.ATTRIBUTES:
            value = getattr(user, attribute, None)
            if not value:
                continue
            value = str(value).lower().lstrip("+")
            if len(value) >= 4 and (value in lowered or lowered in value):
                raise ValidationError(
                    "Parol shaxsiy ma'lumotlaringizga juda o'xshash.",
                    code="password_too_similar",
                )

    def get_help_text(self):
        return "Parol ism yoki telefon raqamingizga o'xshamasin."
