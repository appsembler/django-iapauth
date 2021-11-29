from django.test import TestCase, override_settings
from django.urls import reverse

from iapauth.middleware import StubAuthenticator


class MiddlewareTest(TestCase):
    def test_with_no_header(self):
        """we haven't set a JWT header, so middleware shouldn't be involved"""
        r = self.client.get(reverse("testview"))
        self.assertEqual(r.status_code, 200)
        self.assertTrue("current user: Anonymous" in str(r.content))
        self.assertTrue("is_authenticated: False" in str(r.content))

    @override_settings(JWT_AUDIENCE="/projects/foo")
    def test_invalid_jwt(self):
        headers = {"HTTP_X_GOOG_IAP_JWT_ASSERTION": "totally not a legit JWT"}
        r = self.client.get(reverse("testview"), **headers)
        # invalid JWT on a non-protected view is fine
        self.assertEqual(r.status_code, 200)
        # but we should definitely be logged out
        self.assertTrue("current user: Anonymous" in str(r.content))
        self.assertTrue("is_authenticated: False" in str(r.content))

    @override_settings(JWT_AUDIENCE="/projects/foo")
    def test_invalid_jwt_protected_view(self):
        headers = {"HTTP_X_GOOG_IAP_JWT_ASSERTION": "totally not a legit JWT"}
        r = self.client.get(reverse("protected"), **headers)
        # shouldn't allow us in there
        self.assertEqual(r.status_code, 302)

    @override_settings(
        JWT_AUDIENCE="/projects/foo",
        IAPAUTH_JWT_AUTHENTICATOR=StubAuthenticator(
            True, "testuser@example.com", "example.com"
        ),
    )
    def test_allow_regular_user(self):
        # we have a stubbed out authenticator that will pass
        headers = {"HTTP_X_GOOG_IAP_JWT_ASSERTION": "totally not a legit JWT"}
        r = self.client.get(reverse("testview"), **headers)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("current user: testuser" in str(r.content))
        self.assertTrue("is_authenticated: True" in str(r.content))
        # should not be staff or superuser
        self.assertTrue("is_staff: False" in str(r.content))
        self.assertTrue("is_superuser: False" in str(r.content))

    @override_settings(
        JWT_AUDIENCE="/projects/foo",
        IAPAUTH_JWT_AUTHENTICATOR=StubAuthenticator(
            True, "testuser@example.com", "example.com"
        ),
    )
    def test_allow_regular_user_protected_view(self):
        # should also be able to get in with @login_required view
        headers = {"HTTP_X_GOOG_IAP_JWT_ASSERTION": "totally not a legit JWT"}
        r = self.client.get(reverse("protected"), **headers)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("current user: testuser" in str(r.content))
        self.assertTrue("is_authenticated: True" in str(r.content))

    @override_settings(
        JWT_AUDIENCE="/projects/foo",
        IAPAUTH_JWT_AUTHENTICATOR=StubAuthenticator(
            True, "testuser@example.com", "example.com"
        ),
        IAP_JWT_ADMIN_DOMAIN="example.com",
    )
    def test_superuser_mapping(self):
        # we have a stubbed out authenticator that will pass
        headers = {"HTTP_X_GOOG_IAP_JWT_ASSERTION": "totally not a legit JWT"}
        r = self.client.get(reverse("testview"), **headers)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("current user: testuser" in str(r.content))
        self.assertTrue("is_authenticated: True" in str(r.content))
        # should be staff and superuser
        self.assertTrue("is_staff: True" in str(r.content))
        self.assertTrue("is_superuser: True" in str(r.content))

    @override_settings(
        JWT_AUDIENCE="/projects/foo",
        IAPAUTH_JWT_AUTHENTICATOR=StubAuthenticator(
            True, "testuser@example.com", "example.com"
        ),
    )
    def test_login_twice_valid(self):
        headers = {"HTTP_X_GOOG_IAP_JWT_ASSERTION": "totally not a legit JWT"}
        r = self.client.get(reverse("testview"), **headers)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("current user: testuser" in str(r.content))
        self.assertTrue("is_authenticated: True" in str(r.content))
        # now we access it again and it should still work
        r = self.client.get(reverse("testview"), **headers)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("current user: testuser" in str(r.content))
        self.assertTrue("is_authenticated: True" in str(r.content))

    @override_settings(
        JWT_AUDIENCE="/projects/foo",
        IAPAUTH_JWT_AUTHENTICATOR=StubAuthenticator(
            True, "testuser@example.com", "example.com"
        ),
    )
    def test_login_failure_logs_user_out(self):
        headers = {"HTTP_X_GOOG_IAP_JWT_ASSERTION": "totally not a legit JWT"}
        r = self.client.get(reverse("testview"), **headers)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("current user: testuser" in str(r.content))
        self.assertTrue("is_authenticated: True" in str(r.content))
        # now we access it again, but this time the authentication fails
        with self.settings(
            IAPAUTH_JWT_AUTHENTICATOR=StubAuthenticator(False, None, None),
        ):
            r = self.client.get(reverse("testview"), **headers)
            self.assertEqual(r.status_code, 200)
            # should be logged out
            self.assertTrue("current user: Anonymous" in str(r.content))
            self.assertTrue("is_authenticated: False" in str(r.content))

    @override_settings(
        JWT_AUDIENCE="/projects/foo",
        IAPAUTH_JWT_AUTHENTICATOR=StubAuthenticator(
            True, "testuser@example.com", "example.com"
        ),
    )
    def test_user_mismatch(self):
        """test the case where they are already logged in as one user, then authenticate
        as a different user"""
        headers = {"HTTP_X_GOOG_IAP_JWT_ASSERTION": "totally not a legit JWT"}
        r = self.client.get(reverse("testview"), **headers)
        self.assertEqual(r.status_code, 200)
        self.assertTrue("current user: testuser" in str(r.content))
        self.assertTrue("is_authenticated: True" in str(r.content))
        # now we access it again, but this time the authentication fails
        with self.settings(
            IAPAUTH_JWT_AUTHENTICATOR=StubAuthenticator(
                True, "second@example.com", "example.com"
            )
        ):
            r = self.client.get(reverse("testview"), **headers)
            self.assertEqual(r.status_code, 200)
            # should be logged out of the first one and logged in as the second
            self.assertTrue("current user: second" in str(r.content))
            self.assertTrue("is_authenticated: True" in str(r.content))
