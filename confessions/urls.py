from django.urls import path

from .views import (
    ConfessionListCreateView,
    ConfessionDetailView,
    ReactionCreateView,
    CommentListCreateView,
    NotificationListView,
    NotificationMarkReadView,
    ReportCreateView,
    SecretRecipientSearchView,
    SecretSendCreateView,
)

urlpatterns = [
    # Confessions
    path(
        "",
        ConfessionListCreateView.as_view(),
        name="confession-list-create",
    ),

    path(
        "<int:pk>/",
        ConfessionDetailView.as_view(),
        name="confession-detail",
    ),

    # Reactions
    path(
        "<int:confession_id>/react/",
        ReactionCreateView.as_view(),
        name="confession-react",
    ),

    # Comments
    path(
        "<int:confession_id>/comments/",
        CommentListCreateView.as_view(),
        name="confession-comments",
    ),

    # Notifications
    path(
        "notifications/",
        NotificationListView.as_view(),
        name="notifications",
    ),

    path(
        "notifications/<int:notification_id>/read/",
        NotificationMarkReadView.as_view(),
        name="notification-read",
    ),

    # Reports
    path(
        "<int:confession_id>/report/",
        ReportCreateView.as_view(),
        name="confession-report",
    ),

    # Send Secretly
    path(
        "secret-recipients/",
        SecretRecipientSearchView.as_view(),
        name="secret-recipients",
    ),

    path(
        "<int:confession_id>/send-secret/",
        SecretSendCreateView.as_view(),
        name="send-secret",
    ),
]