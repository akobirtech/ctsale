"""DRF va Django standart xato xabarlarini o'zbekchaga o'girish.

Nega gettext emas: `.po` fayllarni kompilyatsiya qilish uchun serverda
GNU gettext kerak bo'ladi va tarjimalar DRF versiyasi bilan birga
eskiradi. Bu yerda faqat foydalanuvchi ko'radigan xabarlar aniq
qayta yoziladi — qo'shimcha bog'liqlik ham, build qadami ham yo'q.

`apps.core.apps.CoreConfig.ready()` dan bir marta chaqiriladi.
"""

from rest_framework import exceptions as drf_exceptions
from rest_framework import fields, relations, serializers
from rest_framework import validators as drf_validators

# Umumiy maydon xabarlari
COMMON = {
    "required": "Bu maydon to'ldirilishi shart.",
    "null": "Bu maydon bo'sh bo'lishi mumkin emas.",
    "blank": "Bu maydon bo'sh bo'lishi mumkin emas.",
    "invalid": "Noto'g'ri qiymat kiritildi.",
}

FIELD_MESSAGES = {
    fields.Field: COMMON,
    fields.CharField: {
        **COMMON,
        "max_length": "Bu maydon {max_length} ta belgidan oshmasligi kerak.",
        "min_length": "Bu maydon kamida {min_length} ta belgidan iborat bo'lsin.",
    },
    fields.EmailField: {**COMMON, "invalid": "To'g'ri email manzil kiriting."},
    fields.URLField: {**COMMON, "invalid": "To'g'ri havola kiriting."},
    fields.SlugField: {**COMMON, "invalid": "Faqat harf, raqam, tire va pastki chiziq."},
    fields.UUIDField: {**COMMON, "invalid": "Noto'g'ri identifikator."},
    fields.IntegerField: {
        **COMMON,
        "invalid": "To'g'ri butun son kiriting.",
        "max_value": "Qiymat {max_value} dan oshmasligi kerak.",
        "min_value": "Qiymat {min_value} dan kam bo'lmasligi kerak.",
        "max_string_length": "Juda uzun qiymat.",
    },
    fields.FloatField: {
        **COMMON,
        "invalid": "To'g'ri son kiriting.",
        "max_value": "Qiymat {max_value} dan oshmasligi kerak.",
        "min_value": "Qiymat {min_value} dan kam bo'lmasligi kerak.",
    },
    fields.DecimalField: {
        **COMMON,
        "invalid": "To'g'ri son kiriting.",
        "max_value": "Qiymat {max_value} dan oshmasligi kerak.",
        "min_value": "Qiymat {min_value} dan kam bo'lmasligi kerak.",
        "max_digits": "Jami {max_digits} tadan ortiq raqam bo'lmasligi kerak.",
        "max_decimal_places": "Kasr qismida {max_decimal_places} tadan ortiq raqam bo'lmasin.",
        "max_whole_digits": "Butun qismda {max_whole_digits} tadan ortiq raqam bo'lmasin.",
    },
    fields.BooleanField: {**COMMON, "invalid": "\"Ha\" yoki \"yo'q\" qiymatini kiriting."},
    fields.DateField: {
        **COMMON,
        "invalid": "Sanani to'g'ri formatda kiriting (YYYY-MM-DD).",
        "datetime": "Sana kutilgan edi, sana va vaqt emas.",
    },
    fields.DateTimeField: {
        **COMMON,
        "invalid": "Sana va vaqtni to'g'ri formatda kiriting.",
        "date": "Sana va vaqt kutilgan edi.",
    },
    fields.ChoiceField: {
        **COMMON,
        "invalid_choice": "\"{input}\" mumkin bo'lgan variantlardan emas.",
    },
    fields.MultipleChoiceField: {
        **COMMON,
        "invalid_choice": "\"{input}\" mumkin bo'lgan variantlardan emas.",
        "not_a_list": "Ro'yxat kutilgan edi.",
        "empty": "Kamida bitta variant tanlang.",
    },
    fields.FileField: {
        **COMMON,
        "invalid": "Yuborilgan ma'lumot fayl emas.",
        "no_name": "Fayl nomi aniqlanmadi.",
        "empty": "Yuborilgan fayl bo'sh.",
        "max_length": "Fayl nomi juda uzun.",
    },
    fields.ImageField: {
        **COMMON,
        "invalid_image": "Yuklangan fayl to'g'ri rasm emas yoki buzilgan.",
    },
    fields.ListField: {
        **COMMON,
        "not_a_list": "Ro'yxat kutilgan edi.",
        "empty": "Ro'yxat bo'sh bo'lmasligi kerak.",
        "min_length": "Kamida {min_length} ta element bo'lsin.",
        "max_length": "{max_length} tadan ortiq element bo'lmasin.",
    },
    fields.JSONField: {**COMMON, "invalid": "To'g'ri JSON kiriting."},
    relations.PrimaryKeyRelatedField: {
        **COMMON,
        "does_not_exist": "Tanlangan element topilmadi.",
        "incorrect_type": "Noto'g'ri turdagi qiymat.",
    },
    relations.SlugRelatedField: {
        **COMMON,
        "does_not_exist": "Tanlangan element topilmadi.",
        "invalid": "Noto'g'ri qiymat.",
    },
    relations.ManyRelatedField: {
        **COMMON,
        "not_a_list": "Ro'yxat kutilgan edi.",
        "empty": "Kamida bitta element tanlang.",
    },
}

# APIException sinflarining standart matni
EXCEPTION_DETAILS = {
    drf_exceptions.NotAuthenticated: "Bu amal uchun tizimga kirishingiz kerak.",
    drf_exceptions.AuthenticationFailed: "Kirish ma'lumotlari noto'g'ri yoki muddati tugagan.",
    drf_exceptions.PermissionDenied: "Sizda bu amalni bajarish uchun ruxsat yo'q.",
    drf_exceptions.NotFound: "So'ralgan ma'lumot topilmadi.",
    drf_exceptions.MethodNotAllowed: "Bu amal qo'llab-quvvatlanmaydi.",
    drf_exceptions.NotAcceptable: "So'ralgan format qo'llab-quvvatlanmaydi.",
    drf_exceptions.UnsupportedMediaType: "Bu turdagi ma'lumot qabul qilinmaydi.",
    drf_exceptions.Throttled: "Juda ko'p so'rov yuborildi. Biroz kutib turing.",
    drf_exceptions.ParseError: "So'rovni o'qib bo'lmadi. Ma'lumot formatini tekshiring.",
    drf_exceptions.ValidationError: "Yuborilgan ma'lumotda xatolik bor.",
}

VALIDATOR_MESSAGES = {
    drf_validators.UniqueValidator: "Bu qiymat allaqachon band.",
    drf_validators.UniqueTogetherValidator: "Bu ma'lumotlar allaqachon mavjud.",
}


def apply():
    """Xabarlarni o'rnatadi. Bir necha marta chaqirilsa ham zararsiz."""
    for field_class, messages in FIELD_MESSAGES.items():
        # Sinf o'zining lug'atini yangilaymiz; DRF meros olishda
        # ota-sinflardagi xabarlarni ham birlashtiradi.
        field_class.default_error_messages = {
            **getattr(field_class, "default_error_messages", {}),
            **messages,
        }

    for validator_class, message in VALIDATOR_MESSAGES.items():
        validator_class.message = message

    for exception_class, detail in EXCEPTION_DETAILS.items():
        exception_class.default_detail = detail

    # SimpleJWT o'z xabarlarini alohida beradi.
    try:
        from rest_framework_simplejwt import exceptions as jwt_exceptions

        jwt_exceptions.InvalidToken.default_detail = (
            "Sessiya muddati tugagan yoki token yaroqsiz. Qaytadan kiring."
        )
        jwt_exceptions.AuthenticationFailed.default_detail = (
            "Kirish ma'lumotlari noto'g'ri."
        )
    except ImportError:  # pragma: no cover
        pass

    serializers.Serializer.default_error_messages = {
        **getattr(serializers.Serializer, "default_error_messages", {}),
        "invalid": "Yuborilgan ma'lumot noto'g'ri formatda.",
    }
