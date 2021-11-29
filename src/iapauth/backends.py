from django.conf import settings
from django.contrib.auth.backends import RemoteUserBackend


# this expects to be used with IAPJWTAuthMiddleware
class IAPJWTUserBackend(RemoteUserBackend):
    def configure_user(self, request, user):
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
