"""Eski manzillarni 301/410 bilan yopadigan middleware.

Productionda sahifalarni nginx frontendga uzatadi, shuning uchun bu
middleware asosan backend to'g'ridan-to'g'ri ochilgan holatlar uchun
zaxira. SSR server esa 404 chiqqanda `/api/v1/seo/resolve/` ni so'raydi
— ikkalasi ham shu yerdagi bitta `redirects.resolve()` ga tayanadi.
"""

from django.http import HttpResponseGone, HttpResponsePermanentRedirect, HttpResponseRedirect

from . import redirects

# Bu prefikslar hech qachon tekshirilmaydi: API va statik fayllar
# redirect jadvalida bo'lmaydi, har so'rovda kesh so'rash esa isrof.
SKIP_PREFIXES = ("/api/", "/media/", "/static/", "/django-admin/", "/__")


class SeoRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ("GET", "HEAD") and not request.path.startswith(SKIP_PREFIXES):
            response = self._redirect_for(request)
            if response is not None:
                return response
        return self.get_response(request)

    @staticmethod
    def _redirect_for(request):
        decision = redirects.resolve(request.path)
        if decision is None:
            return None

        if decision["status"] == 410:
            return HttpResponseGone("Bu manzil butunlay o'chirilgan.")

        target = decision["target"]
        query = request.META.get("QUERY_STRING")
        if query:
            target = f"{target}?{query}"

        if decision["status"] == 301:
            return HttpResponsePermanentRedirect(target)
        return HttpResponseRedirect(target)
