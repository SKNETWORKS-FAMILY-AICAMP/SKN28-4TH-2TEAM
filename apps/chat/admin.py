from __future__ import annotations

from django.contrib import admin

from apps.chat.models import ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("role", "content", "warning", "route", "created_at")
    fields = ("role", "content", "warning", "route", "created_at")
    can_delete = False


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "user", "is_deleted", "updated_at", "created_at")
    list_filter = ("is_deleted", "created_at", "updated_at")
    search_fields = ("title", "user__username", "user__email")
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "role", "route", "warning", "created_at")
    list_filter = ("role", "route", "warning", "created_at")
    search_fields = ("content", "session__title", "session__user__username")
