"""Audit jurnaliga yozish."""

import logging

from apps.core.utils import get_client_ip

from .models import AuditLog

logger = logging.getLogger(__name__)

# Jurnalda hech qachon ko'rinmasligi kerak bo'lgan maydonlar.
SENSITIVE_FIELDS = {"password", "token", "code_hash", "secret", "search_vector"}


def log_action(
    actor=None,
    action="update",
    target=None,
    target_label="",
    changes=None,
    note="",
    request=None,
):
    """Audit yozuvi yaratadi.

    Hech qachon istisno otmaydi: jurnalga yozib bo'lmagani uchun
    asosiy amal bekor bo'lmasligi kerak.
    """
    try:
        target_type = target_id = ""
        if target is not None:
            target_type = target.__class__.__name__
            target_id = str(getattr(target, "pk", "") or "")

        ip_address = user_agent = None
        if request is not None:
            ip_address = get_client_ip(request) or None
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:255]

        return AuditLog.objects.create(
            actor=actor if getattr(actor, "is_authenticated", False) else None,
            actor_label=str(actor) if actor else "tizim",
            action=action,
            target_type=target_type,
            target_id=target_id,
            target_label=(target_label or str(target or ""))[:200],
            changes=_sanitize(changes or {}),
            note=note[:255],
            ip_address=ip_address,
            user_agent=user_agent or "",
        )
    except Exception:  # pragma: no cover
        logger.exception("Audit yozuvini saqlab bo'lmadi")
        return None


def _sanitize(changes):
    return {
        field: value
        for field, value in changes.items()
        if not any(marker in field.lower() for marker in SENSITIVE_FIELDS)
    }


def diff_instance(before, after, fields):
    """Ikki holat orasidagi farqni {maydon: [eski, yangi]} ko'rinishida."""
    changes = {}
    for field in fields:
        old = before.get(field)
        new = after.get(field)
        if old != new:
            changes[field] = [_serializable(old), _serializable(new)]
    return changes


def _serializable(value):
    if value is None or isinstance(value, (str, int, float, bool, list, dict)):
        return value
    return str(value)
