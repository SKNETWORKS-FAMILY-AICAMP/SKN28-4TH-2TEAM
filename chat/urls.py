from __future__ import annotations

from django.urls import path

from chat import views


urlpatterns = [
    path("", views.chat, name="api_chat"),
    path("sessions/", views.sessions, name="api_chat_sessions"),
    path("sessions/<str:session_id>/", views.session_detail, name="api_chat_session_detail"),
]
