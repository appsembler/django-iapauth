Django authentication middleware and backend for GCP IAP

## install:

```
$ pip install django-iapauth
```

* Add `iapauth` to your `INSTALLED_APPS`.
* Add `iapauth.middleware.IAPJWTAuthMiddleware` to your `MIDDLEWARE`
* Add `iapauth.backends.IAPJWTUserBackend` to your
`AUTHENTICATION_BACKENDS`.

TODO: explain how it works, how to debug, etc.
