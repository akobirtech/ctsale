"""Auth endpointlari.

Token strategiyasi:
  access  — javob tanasida, frontend uni faqat xotirada saqlaydi
  refresh — httpOnly cookie, JavaScript o'qiy olmaydi (XSS himoyasi)
"""

from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from apps.core.exceptions import BusinessError
from apps.core.utils import get_client_ip

from . import services
from .models import OTPPurpose
from .serializers import (
    LoginSerializer,
    OTPRequestSerializer,
    OTPVerifySerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegisterSerializer,
    ShopProfileSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from .throttles import LoginThrottle, OTPThrottle, RegisterThrottle


def _set_refresh_cookie(response, refresh_token):
    response.set_cookie(
        settings.REFRESH_COOKIE_NAME,
        str(refresh_token),
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path=settings.REFRESH_COOKIE_PATH,
    )
    return response


def _clear_refresh_cookie(response):
    response.delete_cookie(
        settings.REFRESH_COOKIE_NAME, path=settings.REFRESH_COOKIE_PATH
    )
    return response


def _token_response(user, extra=None):
    refresh = RefreshToken.for_user(user)
    payload = {
        "access": str(refresh.access_token),
        "expires_in": int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        "user": UserSerializer(user).data,
    }
    if extra:
        payload.update(extra)
    response = Response(payload, status=status.HTTP_200_OK)
    return _set_refresh_cookie(response, refresh)


def _debug_otp(code):
    """Dev rejimida kodni javobga qo'shamiz — SMS provayder yo'q.

    DEBUG=False bo'lganda hech qachon qaytarilmaydi.
    """
    return {"debug_code": code} if settings.DEBUG else {}


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]
    serializer_class = RegisterSerializer

    @extend_schema(request=RegisterSerializer, responses={201: None})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        _, code = services.register_user(
            phone=data["phone"],
            password=data["password"],
            first_name=data.get("first_name", ""),
            last_name=data.get("last_name", ""),
            ip_address=get_client_ip(request),
        )
        return Response(
            {
                "detail": "Tasdiqlash kodi yuborildi.",
                "phone": data["phone"],
                "expires_in": settings.OTP_TTL_SECONDS,
                **_debug_otp(code),
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyPhoneView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPThrottle]
    serializer_class = OTPVerifySerializer

    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.confirm_registration(
            serializer.validated_data["phone"], serializer.validated_data["code"]
        )
        return _token_response(user)


class ResendOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPThrottle]
    serializer_class = OTPRequestSerializer

    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _, code = services.issue_otp(
            serializer.validated_data["phone"],
            OTPPurpose.REGISTER,
            get_client_ip(request),
        )
        return Response(
            {
                "detail": "Yangi kod yuborildi.",
                "expires_in": settings.OTP_TTL_SECONDS,
                **_debug_otp(code),
            }
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.authenticate_user(
            phone=serializer.validated_data["phone"],
            password=serializer.validated_data["password"],
            ip_address=get_client_ip(request),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
        )
        return _token_response(user)


class RefreshView(APIView):
    """Cookie'dagi refresh token orqali yangi access oladi.

    Refresh rotation yoqilgan: har chaqiruvda yangi refresh beriladi,
    eskisi blacklist'ga tushadi.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME) or request.data.get("refresh")
        if not raw:
            raise BusinessError(
                "Sessiya topilmadi. Qaytadan kiring.", code="no_refresh_token", status_code=401
            )

        try:
            refresh = RefreshToken(raw)
        except TokenError:
            response = Response(
                {
                    "error": {
                        "code": "invalid_refresh_token",
                        "message": "Sessiya muddati tugagan. Qaytadan kiring.",
                        "details": {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
            return _clear_refresh_cookie(response)

        access = str(refresh.access_token)
        try:
            refresh.blacklist()
        except AttributeError:  # pragma: no cover - blacklist app o'chirilgan bo'lsa
            pass

        from .models import User

        user = User.objects.filter(pk=refresh.payload.get("user_id")).first()
        if user is None or user.ban_is_active or not user.is_active:
            response = Response(
                {
                    "error": {
                        "code": "account_unavailable",
                        "message": "Hisob mavjud emas yoki bloklangan.",
                        "details": {},
                    }
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
            return _clear_refresh_cookie(response)

        new_refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "access": access,
                "expires_in": int(
                    settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
                ),
            }
        )
        return _set_refresh_cookie(response, new_refresh)


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        raw = request.COOKIES.get(settings.REFRESH_COOKIE_NAME) or request.data.get("refresh")
        if raw:
            try:
                RefreshToken(raw).blacklist()
            except (TokenError, AttributeError):
                # Token allaqachon yaroqsiz — chiqish baribir muvaffaqiyatli.
                pass
        response = Response({"detail": "Tizimdan chiqdingiz."})
        return _clear_refresh_cookie(response)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class ShopProfileView(APIView):
    """Do'kon profili: sotuvchi o'zi boshqaradi.

    Profil ixtiyoriy — jismoniy shaxs sotuvchiga kerak emas. Shuning
    uchun u avtomatik yaratilmaydi: birinchi PUT so'rovida paydo
    bo'ladi.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ShopProfileSerializer

    def get(self, request):
        shop = getattr(request.user, "shop", None)
        if shop is None:
            return Response({"detail": "Do'kon profili yaratilmagan."}, status=404)
        return Response(ShopProfileSerializer(shop, context={"request": request}).data)

    def put(self, request):
        return self._save(request, partial=False)

    def patch(self, request):
        return self._save(request, partial=True)

    def _save(self, request, partial):
        shop = getattr(request.user, "shop", None)
        serializer = ShopProfileSerializer(
            shop, data=request.data, partial=partial and shop is not None,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=200 if shop else 201)

    def delete(self, request):
        shop = getattr(request.user, "shop", None)
        if shop is not None:
            shop.delete()
        return Response(status=204)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PasswordChangeSerializer

    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password", "updated_at"])
        services.revoke_all_refresh_tokens(user)

        # Parol o'zgardi — boshqa qurilmalardagi sessiyalar yopildi,
        # shuning uchun joriy qurilmaga yangi juftlik beramiz.
        return _token_response(user, {"detail": "Parol o'zgartirildi."})


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPThrottle]
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        _, code = services.request_password_reset(
            serializer.validated_data["phone"], get_client_ip(request)
        )
        # Raqam mavjudligidan qat'i nazar bir xil javob — hisob
        # borligini aniqlash imkonini bermaslik uchun.
        return Response(
            {
                "detail": "Agar bu raqam ro'yxatdan o'tgan bo'lsa, tasdiqlash kodi yuborildi.",
                "expires_in": settings.OTP_TTL_SECONDS,
                **(_debug_otp(code) if code else {}),
            }
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [OTPThrottle]
    serializer_class = PasswordResetConfirmSerializer

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = services.confirm_password_reset(
            serializer.validated_data["phone"],
            serializer.validated_data["code"],
            serializer.validated_data["new_password"],
        )
        return _token_response(user, {"detail": "Parol yangilandi."})
