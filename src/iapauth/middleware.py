import os

import jose
import requests
from django.conf import settings
from django.contrib import auth
from django.contrib.auth import load_backend
from django.contrib.auth.backends import RemoteUserBackend
from django.core.exceptions import ImproperlyConfigured
from django.utils.deprecation import MiddlewareMixin
from jose import jwt


KEYS = None  # Cached public keys for verification
AUDIENCE = None  # Cached value requiring information from metadata server


# Google publishes the public keys needed to verify a JWT. Save them in KEYS.
def keys():
    global KEYS

    if KEYS is None:
        resp = requests.get("https://www.gstatic.com/iap/verify/public_key")
        KEYS = resp.json()

    return KEYS


# Returns the JWT "audience" that should be in the assertion
def gcp_jwt_audience():
    global AUDIENCE

    if AUDIENCE is None:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", None)

        endpoint = "http://metadata.google.internal"
        path = "/computeMetadata/v1/project/numeric-project-id"
        response = requests.get(
            "{}/{}".format(endpoint, path), headers={"Metadata-Flavor": "Google"}
        )
        project_number = response.json()

        AUDIENCE = "/projects/{}/apps/{}".format(project_number, project_id)

    return AUDIENCE


class JWTAuthenticator(object):
    def authenticate(self, jwt_token, audience):
        try:
            info = jwt.decode(
                jwt_token,
                keys(),
                algorithms=["ES256"],
                audience=audience,
            )
            return (True, info["email"], info["hd"])
        except jose.exceptions.JOSEError as e:
            # log it
            print("bad JWT: {}".format(e))
        return (False, None, None)


class StubAuthenticator(object):
    """ stub for testing """
    def __init__(self, status=True, email="foo@example.com", domain="example.com"):
        self.response = (status, email, domain)

    def authenticate(self, jwt_token, audience):
        return self.response


class IAPJWTAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # AuthenticationMiddleware is required so that request.user exists.
        if not hasattr(request, "user"):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the RemoteUserMiddleware class."
            )
        request.jwt_user_email = None
        request.jwt_domain = None
        request.jwt_authenticated = False

        jwt_token = request.META.get("HTTP_X_GOOG_IAP_JWT_ASSERTION", None)

        if not jwt_token:
            # no token. We have no responsibility here
            return
        if hasattr(settings, "JWT_AUDIENCE"):
            audience = settings.JWT_AUDIENCE
        else:
            audience = gcp_jwt_audience()

        # we can override the authenticator for testing
        authenticator = JWTAuthenticator()
        if hasattr(settings, "IAPAUTH_JWT_AUTHENTICATOR"):
            authenticator = settings.IAPAUTH_JWT_AUTHENTICATOR

        authenticated, email, domain = authenticator.authenticate(jwt_token, audience)
        if authenticated:
            request.jwt_user_email = email
            request.jwt_domain = domain
            request.jwt_authenticated = True
        else:
            # they tried to use a bad JWT. Make sure they
            # are logged out.
            self._ensure_logged_out(request)
            return

        username = self.clean_username(request.jwt_user_email, request)
        # If the user is already authenticated and that user is the user we are
        # getting passed in the headers, then the correct user is already
        # persisted in the session and we don't need to continue.
        if request.user.is_authenticated:
            if request.user.get_username() == username:
                return
            else:
                # An authenticated user is associated with the request, but
                # it does not match the authorized user in the header.
                self._remove_invalid_user(request)

        # We are seeing this user for the first time in this session, attempt
        # to authenticate the user.
        user = auth.authenticate(request, remote_user=username)
        if user:
            # User is valid.  Set request.user and persist user in the session
            # by logging the user in.
            request.user = user
            auth.login(request, user)

    def _ensure_logged_out(self, request):
        request.jwt_authenticated = False
        request.jwt_domain = None
        request.jwt_user_email = None
        if request.user.is_authenticated:
            self._remove_invalid_user(request)

    def clean_username(self, username, request):
        return username.split("@")[0]

    def _remove_invalid_user(self, request):
        """
        Remove the current authenticated user in the request which is invalid
        but only if the user is authenticated via the RemoteUserBackend.
        """
        try:
            stored_backend = load_backend(
                request.session.get(auth.BACKEND_SESSION_KEY, "")
            )
        except ImportError:
            # backend failed to load
            auth.logout(request)
        else:
            if isinstance(stored_backend, RemoteUserBackend):
                auth.logout(request)
