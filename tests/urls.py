from django.urls import path

from . import views


urlpatterns = [
    path("test", views.testview, name="testview"),
    path("protected", views.protected, name="protected"),
]
