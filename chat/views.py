from __future__ import annotations

import json
from typing import Any

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from chat.models import ChatMessage, ChatSession
from chat.services import answer_question, make_title


ANON_SESSION_KEY = "anonymous_chat_sessions"
ANON_NEXT_ID_KEY = "anonymous_chat_next_id"


def _json_body(request: HttpRequest) -> dict[str, Any]:
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}

    return data if isinstance(data, dict) else {}


def _clean_question(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _validate_question(question: str) -> JsonResponse | None:
    if not question:
        return JsonResponse(
            {"ok": False, "error": "질문을 입력해 주세요."},
            status=400,
        )

    if len(question) > settings.RAG_MAX_QUESTION_LENGTH:
        return JsonResponse(
            {
                "ok": False,
                "error": f"질문은 {settings.RAG_MAX_QUESTION_LENGTH}자 이내로 입력해 주세요.",
            },
            status=400,
        )

    return None


def _session_day(updated_at) -> str:
    local_date = timezone.localtime(updated_at).date()
    today = timezone.localdate()

    if local_date == today:
        return "오늘"

    return local_date.strftime("%Y-%m-%d")


def _session_meta(updated_at, message_count: int = 0) -> str:
    time_label = timezone.localtime(updated_at).strftime("%H:%M")

    if message_count:
        return f"{message_count}개 메시지 · {time_label}"

    return f"{time_label}"


def _db_session_payload(session: ChatSession) -> dict[str, Any]:
    message_count = getattr(session, "message_count", None)

    if message_count is None:
        message_count = session.messages.count()

    return {
        "id": session.id,
        "title": session.title,
        "meta": _session_meta(session.updated_at, message_count),
        "day": _session_day(session.updated_at),
        "icon": "message",
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "temporary": False,
    }


def _db_message_payload(message: ChatMessage) -> dict[str, Any]:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "sources": message.sources,
        "warning": message.warning or None,
        "route": message.route,
        "metadata": message.metadata,
        "created_at": message.created_at.isoformat(),
    }


def _anon_store(request: HttpRequest) -> dict[str, Any]:
    store = request.session.get(ANON_SESSION_KEY)

    if not isinstance(store, dict):
        store = {}
        request.session[ANON_SESSION_KEY] = store

    return store


def _new_anon_id(request: HttpRequest) -> str:
    next_id = int(request.session.get(ANON_NEXT_ID_KEY, 1))
    request.session[ANON_NEXT_ID_KEY] = next_id + 1
    return str(next_id)


def _anon_session_payload(session_id: str, session: dict[str, Any]) -> dict[str, Any]:
    messages = session.get("messages", [])

    return {
        "id": session_id,
        "title": session.get("title") or "새 대화",
        "meta": f"{len(messages)}개 메시지 · 임시",
        "day": "임시 대화",
        "icon": "message",
        "created_at": session.get("created_at", ""),
        "updated_at": session.get("updated_at", ""),
        "temporary": True,
    }


def _anon_message_payload(message: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": message.get("id"),
        "role": message.get("role"),
        "content": message.get("content", ""),
        "sources": message.get("sources", []),
        "warning": message.get("warning"),
        "route": message.get("route", ""),
        "metadata": message.get("metadata", {}),
        "created_at": message.get("created_at", ""),
    }


@require_http_methods(["GET", "POST"])
def sessions(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        if request.user.is_authenticated:
            sessions_qs = (
                ChatSession.objects.filter(user=request.user, is_deleted=False)
                .prefetch_related("messages")
                .order_by("-updated_at", "-id")
            )
            return JsonResponse(
                {
                    "ok": True,
                    "authenticated": True,
                    "sessions": [_db_session_payload(session) for session in sessions_qs],
                }
            )

        store = _anon_store(request)
        payloads = [
            _anon_session_payload(session_id, session)
            for session_id, session in store.items()
        ]
        payloads.sort(key=lambda item: item.get("updated_at") or "", reverse=True)

        return JsonResponse(
            {
                "ok": True,
                "authenticated": False,
                "sessions": payloads,
            }
        )

    if request.user.is_authenticated:
        session = ChatSession.objects.create(
            user=request.user,
            title="새 대화",
        )

        return JsonResponse(
            {
                "ok": True,
                "session": _db_session_payload(session),
            },
            status=201,
        )

    store = _anon_store(request)
    session_id = _new_anon_id(request)
    now = timezone.now().isoformat()
    store[session_id] = {
        "title": "새 대화",
        "messages": [],
        "previous_department_code": "",
        "pending_clarification": {},
        "created_at": now,
        "updated_at": now,
    }
    request.session.modified = True

    return JsonResponse(
        {
            "ok": True,
            "session": _anon_session_payload(session_id, store[session_id]),
        },
        status=201,
    )


@require_http_methods(["GET", "DELETE"])
def session_detail(request: HttpRequest, session_id: str) -> JsonResponse:
    if request.user.is_authenticated:
        try:
            session = ChatSession.objects.get(
                id=session_id,
                user=request.user,
                is_deleted=False,
            )
        except (ChatSession.DoesNotExist, ValueError):
            return JsonResponse({"ok": False, "error": "대화를 찾을 수 없습니다."}, status=404)

        if request.method == "DELETE":
            session.is_deleted = True
            session.save(update_fields=["is_deleted", "updated_at"])
            return JsonResponse({"ok": True})

        return JsonResponse(
            {
                "ok": True,
                "session": _db_session_payload(session),
                "messages": [
                    _db_message_payload(message)
                    for message in session.messages.all()
                ],
            }
        )

    store = _anon_store(request)
    session = store.get(str(session_id))

    if session is None:
        return JsonResponse({"ok": False, "error": "대화를 찾을 수 없습니다."}, status=404)

    if request.method == "DELETE":
        store.pop(str(session_id), None)
        request.session.modified = True
        return JsonResponse({"ok": True})

    return JsonResponse(
        {
            "ok": True,
            "session": _anon_session_payload(str(session_id), session),
            "messages": [
                _anon_message_payload(message)
                for message in session.get("messages", [])
            ],
        }
    )


@require_http_methods(["POST"])
def chat(request: HttpRequest) -> JsonResponse:
    data = _json_body(request)
    question = _clean_question(data.get("question"))
    validation_error = _validate_question(question)

    if validation_error:
        return validation_error

    session_id = data.get("session_id")

    if request.user.is_authenticated:
        response = _chat_authenticated(
            request=request,
            session_id=session_id,
            question=question,
        )
    else:
        response = _chat_anonymous(
            request=request,
            session_id=session_id,
            question=question,
        )

    return JsonResponse(response)


def _chat_authenticated(
    request: HttpRequest,
    session_id: Any,
    question: str,
) -> dict[str, Any]:
    session = None

    if session_id:
        try:
            session = ChatSession.objects.get(
                id=session_id,
                user=request.user,
                is_deleted=False,
            )
        except (ChatSession.DoesNotExist, ValueError):
            session = None

    if session is None:
        session = ChatSession.objects.create(
            user=request.user,
            title=make_title(question),
        )
    elif session.title == "새 대화":
        session.title = make_title(question)

    ChatMessage.objects.create(
        session=session,
        role=ChatMessage.ROLE_USER,
        content=question,
    )

    result = answer_question(
        question=question,
        previous_department_code=session.previous_department_code,
    )

    if result.department_code:
        session.previous_department_code = result.department_code

    session.pending_clarification = result.pending_clarification
    session.save(
        update_fields=[
            "title",
            "previous_department_code",
            "pending_clarification",
            "updated_at",
        ]
    )

    assistant_message = ChatMessage.objects.create(
        session=session,
        role=ChatMessage.ROLE_ASSISTANT,
        content=result.answer,
        sources=result.sources,
        warning=result.warning or "",
        route=result.route,
        metadata=result.metadata,
    )

    return {
        "session_id": session.id,
        "message_id": assistant_message.id,
        "answer": result.answer,
        "sources": result.sources,
        "warning": result.warning,
        "route": result.route,
    }


def _chat_anonymous(
    request: HttpRequest,
    session_id: Any,
    question: str,
) -> dict[str, Any]:
    store = _anon_store(request)
    session_key = str(session_id or "")
    session = store.get(session_key)

    if not session:
        session_key = _new_anon_id(request)
        now = timezone.now().isoformat()
        session = {
            "title": make_title(question),
            "messages": [],
            "previous_department_code": "",
            "pending_clarification": {},
            "created_at": now,
            "updated_at": now,
        }
        store[session_key] = session
    elif session.get("title") == "새 대화":
        session["title"] = make_title(question)

    now = timezone.now().isoformat()
    user_message_id = len(session.get("messages", [])) + 1
    session.setdefault("messages", []).append(
        {
            "id": user_message_id,
            "role": ChatMessage.ROLE_USER,
            "content": question,
            "sources": [],
            "warning": None,
            "route": "",
            "metadata": {},
            "created_at": now,
        }
    )

    result = answer_question(
        question=question,
        previous_department_code=session.get("previous_department_code") or "",
    )

    if result.department_code:
        session["previous_department_code"] = result.department_code

    session["pending_clarification"] = result.pending_clarification
    session["updated_at"] = timezone.now().isoformat()

    assistant_message_id = len(session.get("messages", [])) + 1
    session["messages"].append(
        {
            "id": assistant_message_id,
            "role": ChatMessage.ROLE_ASSISTANT,
            "content": result.answer,
            "sources": result.sources,
            "warning": result.warning,
            "route": result.route,
            "metadata": result.metadata,
            "created_at": session["updated_at"],
        }
    )
    request.session.modified = True

    return {
        "session_id": session_key,
        "message_id": assistant_message_id,
        "answer": result.answer,
        "sources": result.sources,
        "warning": result.warning,
        "route": result.route,
    }
