from __future__ import annotations

from django.contrib import admin
from django.urls import include, path
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.generic import TemplateView


login_page = ensure_csrf_cookie(
    TemplateView.as_view(template_name="accounts/login.html")
)
signup_page = ensure_csrf_cookie(
    TemplateView.as_view(template_name="accounts/signup.html")
)
chat_page = ensure_csrf_cookie(
    TemplateView.as_view(template_name="chat/chat.html")
)
admin_stats_page = ensure_csrf_cookie(
    TemplateView.as_view(template_name="dashboard/admin_stats.html")
)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("kaist_rag.apps.accounts.urls")),
    path("api/chat/", include("kaist_rag.apps.chat.urls")),
    path("", login_page, name="home"),
    path("login/", login_page, name="login"),
    path("signup/", signup_page, name="signup"),
    path("chat/", chat_page, name="chat"),
    path("admin-stats/", admin_stats_page, name="admin_stats"),
]
