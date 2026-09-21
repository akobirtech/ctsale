"""Xavfsizlik headerlari va yengil foydalanuvchi kuzatuvi."""

from django.conf import settings
from django.utils import timezone


class SecurityHeadersMiddleware:
    """Django SecurityMiddleware qamramaydigan headerlarni qo'shadi.

    CSP, Permissions-Policy va COOP/CORP — Django'da tayyor sozlamasi
    yo'q, shuning uchun bu yerda aniq ko'rinadigan qilib yoziladi.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.csp_value = self._build_csp()
        self.csp_header = (
            "Content-Security-Policy-Report-Only"
            if getattr(settings, "CSP_REPORT_ONLY", False)
            else "Content-Security-Policy"
        )

    @staticmethod
    def _build_csp():
        directives = getattr(settings, "CSP_DIRECTIVES", {})
        parts = []
        for name, sources in directives.items():
            if not sources:
                continue
            parts.append(f"{name} {' '.join(sources)}")
        return "; ".join(parts)

    def __call__(self, request):
        response = self.get_response(request)

        if self.csp_value and self.csp_header not in response:
            response[self.csp_header] = self.csp_value

        response.setdefault("X-Content-Type-Options", "nosniff")
        response.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.setdefault(
            "Permissions-Policy", getattr(settings, "PERMISSIONS_POLICY", "")
        )
        response.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        # Media fayllar boshqa domendagi frontenddan yuklanadi, shuning
        # uchun resurs siyosati cross-origin bo'lishi kerak.
        response.setdefault("Cross-Origin-Resource-Policy", "cross-origin")

        # `Server` headeri bu yerdan boshqarilmaydi: uni HTTP server
        # (dev'da WSGIServer, productionda gunicorn/nginx) middleware
        # ishlagandan KEYIN qo'yadi. Yashirish nginx darajasida
        # qilinadi — `server_tokens off` va `proxy_hide_header Server`
        # (deploy/nginx/*.conf).

        # Maxfiy javoblarni oraliq kesh saqlamasin.
        if request.path.startswith("/api/") and request.user.is_authenticated:
            response.setdefault("Cache-Control", "no-store, private")

        return response


class LastSeenMiddleware:
    """Foydalanuvchining oxirgi faolligini kuniga bir marta yangilaydi.

    Har so'rovda UPDATE qilish bazaga keraksiz yuk bo'lardi, shuning
    uchun bir kunlik aniqlik yetarli deb hisoblanadi.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated:
            now = timezone.now()
            last = user.last_seen_at
            if last is None or (now - last).total_seconds() > 86400:
                type(user).objects.filter(pk=user.pk).update(last_seen_at=now)

        return response
