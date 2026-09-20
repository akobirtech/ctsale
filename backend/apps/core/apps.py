from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    label = "core"

    def ready(self):
        # DRF standart xato xabarlarini o'zbekchaga almashtiramiz.
        from . import drf_messages

        drf_messages.apply()
