from __future__ import annotations

import json
import math
from typing import Any

from django.db.models import Count, F, Q
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from kaist_rag.apps.community.models import (
    CommunityComment,
    CommunityInquiry,
    CommunityPost,
)


PAGE_SIZE = 5
MAX_PAGE_SIZE = 20


def _json_body(request: HttpRequest) -> dict[str, Any]:
    try:
        data = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return {}

    return data if isinstance(data, dict) else {}


def _text(value: Any, limit: int | None = None) -> str:
    cleaned = " ".join(str(value or "").strip().split())
    if limit is not None:
        return cleaned[:limit]
    return cleaned


def _content(value: Any) -> str:
    return str(value or "").strip()


def _page_params(request: HttpRequest) -> tuple[int, int]:
    try:
        page = int(request.GET.get("page", "1"))
    except ValueError:
        page = 1

    try:
        page_size = int(request.GET.get("page_size", str(PAGE_SIZE)))
    except ValueError:
        page_size = PAGE_SIZE

    return max(1, page), min(max(1, page_size), MAX_PAGE_SIZE)


def _user_name(user) -> str:
    return user.get_full_name() or user.first_name or user.email or user.username


def _date_label(value) -> str:
    return timezone.localtime(value).strftime("%Y-%m-%d %H:%M")


def _summary(content: str) -> str:
    one_line = " ".join(str(content or "").strip().split())
    return one_line[:120] + ("..." if len(one_line) > 120 else "")


def _is_admin(request: HttpRequest) -> bool:
    return bool(request.user.is_authenticated and request.user.is_staff)


def _can_manage(request: HttpRequest, author) -> bool:
    return bool(request.user.is_authenticated and (_is_admin(request) or author_id(author) == request.user.id))


def author_id(author) -> int | None:
    return getattr(author, "id", None)


def _auth_required(request: HttpRequest) -> JsonResponse | None:
    if request.user.is_authenticated:
        return None

    return JsonResponse({"ok": False, "error": "로그인이 필요합니다."}, status=401)


def _post_qs():
    return (
        CommunityPost.objects.filter(is_deleted=False)
        .select_related("author")
        .annotate(comment_count=Count("comments", filter=Q(comments__is_deleted=False)))
    )


def _inquiry_qs(request: HttpRequest):
    qs = (
        CommunityInquiry.objects.filter(is_deleted=False)
        .select_related("author")
        .annotate(comment_count=Count("comments", filter=Q(comments__is_deleted=False)))
    )

    if _is_admin(request):
        return qs

    if request.user.is_authenticated:
        return qs.filter(Q(is_private=False) | Q(author=request.user))

    return qs.filter(is_private=False)


def _post_payload(post: CommunityPost, request: HttpRequest, detail: bool = False) -> dict[str, Any]:
    comment_count = getattr(post, "comment_count", None)
    if comment_count is None:
        comment_count = post.comments.filter(is_deleted=False).count()

    payload = {
        "id": post.id,
        "category": post.category,
        "badge": "공지" if post.is_notice else "게시글",
        "title": post.title,
        "summary": _summary(post.content),
        "author": _user_name(post.author),
        "authorId": post.author_id,
        "date": _date_label(post.created_at),
        "views": post.view_count,
        "comments": comment_count,
        "icon": "book",
        "isNotice": post.is_notice,
        "isCommentBlocked": post.is_comment_blocked,
        "referenceUrl": post.reference_url,
        "createdAt": post.created_at.isoformat(),
        "updatedAt": post.updated_at.isoformat(),
        "canManage": _can_manage(request, post.author),
        "canComment": not post.is_comment_blocked,
    }

    if detail:
        payload["content"] = post.content
        payload["replies"] = [
            _comment_payload(comment, request)
            for comment in post.comments.filter(is_deleted=False).select_related("author")
        ]

    return payload


def _inquiry_payload(inquiry: CommunityInquiry, request: HttpRequest, detail: bool = False) -> dict[str, Any]:
    comment_count = getattr(inquiry, "comment_count", None)
    if comment_count is None:
        comment_count = inquiry.comments.filter(is_deleted=False).count()

    payload = {
        "id": inquiry.id,
        "category": inquiry.category,
        "status": inquiry.status,
        "statusText": inquiry.get_status_display(),
        "title": inquiry.title,
        "summary": _summary(inquiry.content),
        "author": _user_name(inquiry.author),
        "authorId": inquiry.author_id,
        "date": _date_label(inquiry.created_at),
        "views": inquiry.view_count,
        "comments": comment_count,
        "isPrivate": inquiry.is_private,
        "emailOnAnswer": inquiry.email_on_answer,
        "createdAt": inquiry.created_at.isoformat(),
        "updatedAt": inquiry.updated_at.isoformat(),
        "canManage": _can_manage(request, inquiry.author),
        "canChangeStatus": _is_admin(request),
    }

    if detail:
        payload["content"] = inquiry.content
        payload["replies"] = [
            _comment_payload(comment, request)
            for comment in inquiry.comments.filter(is_deleted=False).select_related("author")
        ]

    return payload


def _comment_payload(comment: CommunityComment, request: HttpRequest) -> dict[str, Any]:
    return {
        "id": comment.id,
        "author": _user_name(comment.author),
        "authorId": comment.author_id,
        "body": comment.content,
        "date": _date_label(comment.created_at),
        "createdAt": comment.created_at.isoformat(),
        "updatedAt": comment.updated_at.isoformat(),
        "canManage": _can_manage(request, comment.author),
    }


def _validate_post_payload(data: dict[str, Any]) -> tuple[dict[str, Any] | None, JsonResponse | None]:
    category = _text(data.get("category"), 40)
    title = _text(data.get("title"), 160)
    content = _content(data.get("content"))
    reference_url = _text(data.get("referenceUrl") or data.get("reference_url"), 500)

    if not category:
        return None, JsonResponse({"ok": False, "error": "카테고리를 입력해 주세요."}, status=400)
    if not title:
        return None, JsonResponse({"ok": False, "error": "제목을 입력해 주세요."}, status=400)
    if not content:
        return None, JsonResponse({"ok": False, "error": "본문을 입력해 주세요."}, status=400)

    return {
        "category": category,
        "title": title,
        "content": content,
        "reference_url": reference_url,
    }, None


def _validate_inquiry_payload(data: dict[str, Any]) -> tuple[dict[str, Any] | None, JsonResponse | None]:
    category = _text(data.get("category"), 40)
    title = _text(data.get("title"), 160)
    content = _content(data.get("content"))

    if not category:
        return None, JsonResponse({"ok": False, "error": "문의 유형을 선택해 주세요."}, status=400)
    if not title:
        return None, JsonResponse({"ok": False, "error": "제목을 입력해 주세요."}, status=400)
    if not content:
        return None, JsonResponse({"ok": False, "error": "문의 내용을 입력해 주세요."}, status=400)

    return {
        "category": category,
        "title": title,
        "content": content,
        "is_private": bool(data.get("isPrivate", True)),
        "email_on_answer": False,
    }, None


@require_http_methods(["GET", "POST"])
def posts(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        auth_error = _auth_required(request)
        if auth_error:
            return auth_error

        data = _json_body(request)
        payload, error = _validate_post_payload(data)
        if error:
            return error

        assert payload is not None
        post = CommunityPost.objects.create(
            author=request.user,
            **payload,
            is_notice=bool(data.get("isNotice", False)) if _is_admin(request) else False,
            is_comment_blocked=bool(data.get("isCommentBlocked", False)) if _is_admin(request) else False,
        )

        return JsonResponse({"ok": True, "post": _post_payload(post, request, detail=True)}, status=201)

    page, page_size = _page_params(request)
    query = _text(request.GET.get("q"))
    qs = _post_qs()

    if query:
        qs = qs.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(category__icontains=query)
            | Q(author__first_name__icontains=query)
            | Q(author__email__icontains=query)
            | Q(author__username__icontains=query)
        )

    total = qs.count()
    pages = max(1, math.ceil(total / page_size))
    page = min(page, pages)

    notices = list(qs.filter(is_notice=True).order_by("-created_at", "-id")[:3])
    notice_ids = [post.id for post in notices]
    regular_qs = qs.exclude(id__in=notice_ids).order_by("-created_at", "-id")

    if page == 1:
        items = notices + list(regular_qs[: max(0, page_size - len(notices))])
    else:
        offset = max(0, (page - 1) * page_size - len(notices))
        items = list(regular_qs[offset : offset + page_size])

    return JsonResponse(
        {
            "ok": True,
            "posts": [_post_payload(post, request) for post in items],
            "count": total,
            "page": page,
            "pageSize": page_size,
            "pages": pages,
        }
    )


@require_http_methods(["GET", "PATCH", "DELETE"])
def post_detail(request: HttpRequest, post_id: int) -> JsonResponse:
    try:
        post = _post_qs().get(id=post_id)
    except CommunityPost.DoesNotExist:
        return JsonResponse({"ok": False, "error": "게시글을 찾을 수 없습니다."}, status=404)

    if request.method == "GET":
        CommunityPost.objects.filter(id=post.id).update(view_count=F("view_count") + 1)
        post.refresh_from_db()
        post.comment_count = post.comments.filter(is_deleted=False).count()
        return JsonResponse({"ok": True, "post": _post_payload(post, request, detail=True)})

    auth_error = _auth_required(request)
    if auth_error:
        return auth_error

    if not _can_manage(request, post.author):
        return JsonResponse({"ok": False, "error": "수정 권한이 없습니다."}, status=403)

    if request.method == "DELETE":
        post.is_deleted = True
        post.save(update_fields=["is_deleted", "updated_at"])
        return JsonResponse({"ok": True})

    data = _json_body(request)
    payload, error = _validate_post_payload(data)
    if error:
        return error

    assert payload is not None
    for field, value in payload.items():
        setattr(post, field, value)

    update_fields = ["category", "title", "content", "reference_url", "updated_at"]

    if _is_admin(request):
        post.is_notice = bool(data.get("isNotice", False))
        post.is_comment_blocked = bool(data.get("isCommentBlocked", False))
        update_fields += ["is_notice", "is_comment_blocked"]

    post.save(update_fields=update_fields)
    post.comment_count = post.comments.filter(is_deleted=False).count()
    return JsonResponse({"ok": True, "post": _post_payload(post, request, detail=True)})


@require_http_methods(["POST"])
def post_comments(request: HttpRequest, post_id: int) -> JsonResponse:
    auth_error = _auth_required(request)
    if auth_error:
        return auth_error

    try:
        post = CommunityPost.objects.get(id=post_id, is_deleted=False)
    except CommunityPost.DoesNotExist:
        return JsonResponse({"ok": False, "error": "게시글을 찾을 수 없습니다."}, status=404)

    if post.is_comment_blocked:
        return JsonResponse({"ok": False, "error": "댓글이 차단된 게시글입니다."}, status=403)

    content = _content(_json_body(request).get("content"))
    if not content:
        return JsonResponse({"ok": False, "error": "댓글 내용을 입력해 주세요."}, status=400)

    comment = CommunityComment.objects.create(author=request.user, post=post, content=content)
    return JsonResponse({"ok": True, "comment": _comment_payload(comment, request)}, status=201)


@require_http_methods(["GET", "POST"])
def inquiries(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        auth_error = _auth_required(request)
        if auth_error:
            return auth_error

        data = _json_body(request)
        payload, error = _validate_inquiry_payload(data)
        if error:
            return error

        assert payload is not None
        inquiry = CommunityInquiry.objects.create(author=request.user, **payload)
        return JsonResponse({"ok": True, "inquiry": _inquiry_payload(inquiry, request, detail=True)}, status=201)

    page, page_size = _page_params(request)
    query = _text(request.GET.get("q"))
    qs = _inquiry_qs(request)

    if query:
        qs = qs.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(category__icontains=query)
            | Q(status__icontains=query)
            | Q(author__first_name__icontains=query)
            | Q(author__email__icontains=query)
            | Q(author__username__icontains=query)
        )

    total = qs.count()
    pages = max(1, math.ceil(total / page_size))
    page = min(page, pages)
    offset = (page - 1) * page_size
    items = list(qs.order_by("-created_at", "-id")[offset : offset + page_size])

    return JsonResponse(
        {
            "ok": True,
            "inquiries": [_inquiry_payload(inquiry, request) for inquiry in items],
            "count": total,
            "page": page,
            "pageSize": page_size,
            "pages": pages,
        }
    )


@require_http_methods(["GET", "PATCH", "DELETE"])
def inquiry_detail(request: HttpRequest, inquiry_id: int) -> JsonResponse:
    try:
        inquiry = _inquiry_qs(request).get(id=inquiry_id)
    except CommunityInquiry.DoesNotExist:
        return JsonResponse({"ok": False, "error": "문의글을 찾을 수 없습니다."}, status=404)

    if request.method == "GET":
        CommunityInquiry.objects.filter(id=inquiry.id).update(view_count=F("view_count") + 1)
        inquiry.refresh_from_db()
        inquiry.comment_count = inquiry.comments.filter(is_deleted=False).count()
        return JsonResponse({"ok": True, "inquiry": _inquiry_payload(inquiry, request, detail=True)})

    auth_error = _auth_required(request)
    if auth_error:
        return auth_error

    if not _can_manage(request, inquiry.author):
        return JsonResponse({"ok": False, "error": "수정 권한이 없습니다."}, status=403)

    if request.method == "DELETE":
        inquiry.is_deleted = True
        inquiry.save(update_fields=["is_deleted", "updated_at"])
        return JsonResponse({"ok": True})

    data = _json_body(request)
    payload, error = _validate_inquiry_payload(data)
    if error:
        return error

    assert payload is not None
    for field, value in payload.items():
        setattr(inquiry, field, value)
    inquiry.save(update_fields=["category", "title", "content", "is_private", "email_on_answer", "updated_at"])
    inquiry.comment_count = inquiry.comments.filter(is_deleted=False).count()

    return JsonResponse({"ok": True, "inquiry": _inquiry_payload(inquiry, request, detail=True)})


@require_http_methods(["POST"])
def inquiry_comments(request: HttpRequest, inquiry_id: int) -> JsonResponse:
    auth_error = _auth_required(request)
    if auth_error:
        return auth_error

    try:
        inquiry = _inquiry_qs(request).get(id=inquiry_id)
    except CommunityInquiry.DoesNotExist:
        return JsonResponse({"ok": False, "error": "문의글을 찾을 수 없습니다."}, status=404)

    content = _content(_json_body(request).get("content"))
    if not content:
        return JsonResponse({"ok": False, "error": "댓글 내용을 입력해 주세요."}, status=400)

    comment = CommunityComment.objects.create(author=request.user, inquiry=inquiry, content=content)
    return JsonResponse({"ok": True, "comment": _comment_payload(comment, request)}, status=201)


@require_http_methods(["PATCH"])
def inquiry_status(request: HttpRequest, inquiry_id: int) -> JsonResponse:
    auth_error = _auth_required(request)
    if auth_error:
        return auth_error

    if not _is_admin(request):
        return JsonResponse({"ok": False, "error": "관리자만 문의 상태를 변경할 수 있습니다."}, status=403)

    try:
        inquiry = CommunityInquiry.objects.get(id=inquiry_id, is_deleted=False)
    except CommunityInquiry.DoesNotExist:
        return JsonResponse({"ok": False, "error": "문의글을 찾을 수 없습니다."}, status=404)

    status = _text(_json_body(request).get("status"), 20)
    valid_statuses = {value for value, _label in CommunityInquiry.STATUS_CHOICES}

    if status not in valid_statuses:
        return JsonResponse({"ok": False, "error": "올바른 문의 상태가 아닙니다."}, status=400)

    inquiry.status = status
    inquiry.save(update_fields=["status", "updated_at"])
    inquiry.comment_count = inquiry.comments.filter(is_deleted=False).count()

    return JsonResponse({"ok": True, "inquiry": _inquiry_payload(inquiry, request, detail=True)})


@require_http_methods(["PATCH", "DELETE"])
def comment_detail(request: HttpRequest, comment_id: int) -> JsonResponse:
    auth_error = _auth_required(request)
    if auth_error:
        return auth_error

    try:
        comment = CommunityComment.objects.select_related("author", "post", "inquiry").get(
            id=comment_id,
            is_deleted=False,
        )
    except CommunityComment.DoesNotExist:
        return JsonResponse({"ok": False, "error": "댓글을 찾을 수 없습니다."}, status=404)

    if comment.inquiry_id:
        try:
            _inquiry_qs(request).get(id=comment.inquiry_id)
        except CommunityInquiry.DoesNotExist:
            return JsonResponse({"ok": False, "error": "댓글을 찾을 수 없습니다."}, status=404)

    if not _can_manage(request, comment.author):
        return JsonResponse({"ok": False, "error": "댓글 수정 권한이 없습니다."}, status=403)

    if request.method == "DELETE":
        comment.is_deleted = True
        comment.save(update_fields=["is_deleted", "updated_at"])
        return JsonResponse({"ok": True})

    content = _content(_json_body(request).get("content"))
    if not content:
        return JsonResponse({"ok": False, "error": "댓글 내용을 입력해 주세요."}, status=400)

    comment.content = content
    comment.save(update_fields=["content", "updated_at"])
    return JsonResponse({"ok": True, "comment": _comment_payload(comment, request)})


@require_http_methods(["GET"])
def mine(request: HttpRequest) -> JsonResponse:
    auth_error = _auth_required(request)
    if auth_error:
        return auth_error

    posts_qs = (
        _post_qs()
        .filter(author=request.user)
        .order_by("-created_at", "-id")[:20]
    )
    inquiries_qs = (
        _inquiry_qs(request)
        .filter(author=request.user)
        .order_by("-created_at", "-id")[:20]
    )

    return JsonResponse(
        {
            "ok": True,
            "posts": [_post_payload(post, request) for post in posts_qs],
            "inquiries": [_inquiry_payload(inquiry, request) for inquiry in inquiries_qs],
        }
    )
