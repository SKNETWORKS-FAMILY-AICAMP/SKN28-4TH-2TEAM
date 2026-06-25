from __future__ import annotations

from django.conf import settings
from django.db import models
from django.db.models import Q


class CommunityPost(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_posts",
    )
    category = models.CharField(max_length=40)
    title = models.CharField(max_length=160)
    content = models.TextField()
    reference_url = models.URLField(blank=True)
    is_notice = models.BooleanField(default=False)
    is_comment_blocked = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "community_post"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["is_deleted", "-created_at"], name="comm_post_del_created_idx"),
            models.Index(fields=["author", "is_deleted", "-created_at"], name="comm_post_author_idx"),
            models.Index(fields=["is_notice", "is_deleted", "-created_at"], name="comm_post_notice_idx"),
        ]

    def __str__(self) -> str:
        return self.title


class CommunityInquiry(models.Model):
    STATUS_WAIT = "wait"
    STATUS_PROGRESS = "progress"
    STATUS_DONE = "done"
    STATUS_CHOICES = [
        (STATUS_WAIT, "답변 대기"),
        (STATUS_PROGRESS, "처리중"),
        (STATUS_DONE, "답변 완료"),
    ]

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_inquiries",
    )
    category = models.CharField(max_length=40)
    title = models.CharField(max_length=160)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_WAIT)
    is_private = models.BooleanField(default=True)
    email_on_answer = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "community_inquiry"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["status", "is_deleted", "-created_at"], name="comm_inq_status_idx"),
            models.Index(fields=["author", "is_deleted", "-created_at"], name="comm_inq_author_idx"),
            models.Index(fields=["is_private", "is_deleted", "-created_at"], name="comm_inq_private_idx"),
        ]

    def __str__(self) -> str:
        return self.title


class CommunityComment(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="community_comments",
    )
    post = models.ForeignKey(
        CommunityPost,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )
    inquiry = models.ForeignKey(
        CommunityInquiry,
        on_delete=models.CASCADE,
        related_name="comments",
        null=True,
        blank=True,
    )
    content = models.TextField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "community_comment"
        ordering = ["created_at", "id"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(post__isnull=False, inquiry__isnull=True)
                    | Q(post__isnull=True, inquiry__isnull=False)
                ),
                name="community_comment_one_target",
            )
        ]
        indexes = [
            models.Index(fields=["post", "is_deleted", "created_at"], name="comm_cmt_post_idx"),
            models.Index(fields=["inquiry", "is_deleted", "created_at"], name="comm_cmt_inq_idx"),
            models.Index(fields=["author", "is_deleted", "created_at"], name="comm_cmt_author_idx"),
        ]

    def __str__(self) -> str:
        return self.content[:40]
