from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend
from django.contrib.auth.models import User

from .middleware import JWTRequest


try:
    import beeline  # type: ignore
except ImportError:
    import iapauth.instrumentation as beeline  # type: ignore


# this expects to be used with IAPJWTAuthMiddleware
class IAPJWTUserBackend(RemoteUserBackend):
    @beeline.traced(name="iapauth.backend.IAPJWTUserBackend.configure_user")
    def configure_user(self, request: JWTRequest, user: User):
        """
        Configure a user after creation and return the updated user.
        """
        user.email = request.jwt_user_email
        user.set_unusable_password()
        domain = request.jwt_domain
        if hasattr(settings, "IAP_JWT_ADMIN_DOMAIN"):
            if domain == settings.IAP_JWT_ADMIN_DOMAIN:
                user.is_superuser = True
                user.is_staff = True
        user.save()
        return user
