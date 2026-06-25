from __future__ import annotations

from django.urls import path

from kaist_rag.apps.community import views


urlpatterns = [
    path("posts/", views.posts, name="api_community_posts"),
    path("posts/<int:post_id>/", views.post_detail, name="api_community_post_detail"),
    path("posts/<int:post_id>/comments/", views.post_comments, name="api_community_post_comments"),
    path("inquiries/", views.inquiries, name="api_community_inquiries"),
    path("inquiries/<int:inquiry_id>/", views.inquiry_detail, name="api_community_inquiry_detail"),
    path("inquiries/<int:inquiry_id>/comments/", views.inquiry_comments, name="api_community_inquiry_comments"),
    path("inquiries/<int:inquiry_id>/status/", views.inquiry_status, name="api_community_inquiry_status"),
    path("comments/<int:comment_id>/", views.comment_detail, name="api_community_comment_detail"),
    path("mine/", views.mine, name="api_community_mine"),
]

