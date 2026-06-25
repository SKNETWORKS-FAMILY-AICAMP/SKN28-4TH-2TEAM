from __future__ import annotations

from django.contrib import admin

from kaist_rag.apps.community.models import (
    CommunityComment,
    CommunityInquiry,
    CommunityPost,
)


@admin.register(CommunityPost)
class CommunityPostAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "is_notice", "is_comment_blocked", "view_count", "is_deleted", "created_at")
    list_filter = ("category", "is_notice", "is_comment_blocked", "is_deleted", "created_at")
    search_fields = ("title", "content", "author__username", "author__email")


@admin.register(CommunityInquiry)
class CommunityInquiryAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "author", "status", "is_private", "view_count", "is_deleted", "created_at")
    list_filter = ("status", "category", "is_private", "is_deleted", "created_at")
    search_fields = ("title", "content", "author__username", "author__email")


@admin.register(CommunityComment)
class CommunityCommentAdmin(admin.ModelAdmin):
    list_display = ("content", "author", "post", "inquiry", "is_deleted", "created_at")
    list_filter = ("is_deleted", "created_at")
    search_fields = ("content", "author__username", "author__email")

