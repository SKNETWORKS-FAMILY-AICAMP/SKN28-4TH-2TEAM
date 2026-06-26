from __future__ import annotations

import json
from typing import Any

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET, require_POST


def _json_body(request: HttpRequest) -> dict[str, Any]:
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}

    return data if isinstance(data, dict) else {}


def _user_payload(user) -> dict[str, Any]:
    name = user.get_full_name() or user.first_name or user.email or user.username
    email = user.email or user.username

    return {
        "id": user.id,
        "name": name,
        "email": email,
        "initial": (name or email or "?")[:1],
        "role": "admin" if user.is_staff else "user",
    }


@require_GET
def me(request: HttpRequest) -> JsonResponse:
    if not request.user.is_authenticated:
        return JsonResponse(
            {
                "authenticated": False,
                "user": {
                    "name": "게스트",
                    "email": "temporary@session",
                    "initial": "게",
                    "role": "guest",
                },
            }
        )

    return JsonResponse(
        {
            "authenticated": True,
            "user": _user_payload(request.user),
        }
    )


@require_POST
def signup(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    name = str(data.get("name", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))

    if not name:
        return JsonResponse({"ok": False, "field": "name", "error": "이름을 입력해 주세요."}, status=400)

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse(
            {"ok": False, "field": "email", "error": "올바른 이메일 형식을 입력해 주세요."},
            status=400,
        )

    User = get_user_model()

    if User.objects.filter(username__iexact=email).exists() or User.objects.filter(email__iexact=email).exists():
        return JsonResponse(
            {"ok": False, "field": "email", "error": "이미 가입된 이메일입니다."},
            status=409,
        )

    try:
        validate_password(password)
    except ValidationError as exc:
        return JsonResponse({"ok": False, "field": "password", "error": " ".join(exc.messages)}, status=400)

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=name,
    )
    login(request, user)

    return JsonResponse(
        {
            "ok": True,
            "authenticated": True,
            "user": _user_payload(user),
        },
        status=201,
    )


@require_POST
def login_view(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    remember = bool(data.get("remember", False))

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse(
            {"ok": False, "error": "올바른 이메일 형식을 입력해 주세요."},
            status=400,
        )

    user = authenticate(request, username=email, password=password)

    if user is None:
        return JsonResponse(
            {"ok": False, "error": "이메일 또는 비밀번호가 올바르지 않습니다."},
            status=401,
        )

    login(request, user)

    if not remember:
        request.session.set_expiry(0)

    return JsonResponse(
        {
            "ok": True,
            "authenticated": True,
            "user": _user_payload(user),
        }
    )


@require_POST
def logout_view(request: HttpRequest) -> JsonResponse:
    logout(request)
    return JsonResponse({"ok": True, "authenticated": False})
