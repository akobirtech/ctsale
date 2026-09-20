"""Auth endpointlari uchun so'rov chegaralari.

Tezlik qiymatlari settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] da.
"""

from rest_framework.throttling import AnonRateThrottle


class LoginThrottle(AnonRateThrottle):
    scope = "login"


class RegisterThrottle(AnonRateThrottle):
    scope = "register"


class OTPThrottle(AnonRateThrottle):
    scope = "otp"
