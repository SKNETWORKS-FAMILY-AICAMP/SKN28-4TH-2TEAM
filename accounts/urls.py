from __future__ import annotations

from django.urls import path

from accounts import views


urlpatterns = [
    path("me/", views.me, name="api_auth_me"),
    path("signup/", views.signup, name="api_auth_signup"),
    path("login/", views.login_view, name="api_auth_login"),
    path("logout/", views.logout_view, name="api_auth_logout"),
]
