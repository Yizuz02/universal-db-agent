from django.urls import path

from .page_views import UserLoginView, ChatView
from .api_views import (
    ConversationDetailView,
    ConversationListView,
    ProcessAgentMessageView,
    ViewMarkdownReportView,
    FileDownloadView,
    FilePreviewView,
)

urlpatterns = [
    # HTML pages
    path("", UserLoginView.as_view(), name="login"),

    path("chat/", ChatView.as_view(), name="chat"),
    
    path(
        "chat/<int:conversation_id>/",
        ChatView.as_view(),
        name="conversation",
    ),

    # API
    path(
        "api/conversations/",
        ConversationListView.as_view(),
        name="conversation-list",
    ),
    path(
        "api/conversations/<int:conversation_id>/",
        ConversationDetailView.as_view(),
        name="conversation-detail",
    ),
    path(
        "api/conversations/<int:conversation_id>/messages/",
        ProcessAgentMessageView.as_view(),
        name="process-agent-message",
    ),
    path(
        "api/reports/<str:filename>/",
        ViewMarkdownReportView.as_view(),
        name="view-report",
    ),
    path(
        "api/files/<int:file_id>/download/",
        FileDownloadView.as_view(),
        name="file-download",
    ),
    path(
        "api/files/<int:file_id>/preview/",
        FilePreviewView.as_view(),
        name="file-preview",
    ),
]