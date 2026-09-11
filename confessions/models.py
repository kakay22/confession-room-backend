from django.contrib.auth.models import User
from django.db import models
import uuid
from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    anonymous_username = models.CharField(
        max_length=30,
        unique=True
    )

    anonymous_avatar = models.CharField(
        max_length=50,
        default="avatar1"
    )

    def __str__(self):
        return self.anonymous_username


# class Confession(models.Model):
#     author = models.ForeignKey(
#         User,
#         on_delete=models.CASCADE,
#         related_name="confessions"
#     )

#     content = models.TextField()

#     status = models.CharField(
#         max_length=20,
#         choices=[
#             ("PUBLISHED", "Published"),
#             ("PENDING", "Pending"),
#             ("HIDDEN", "Hidden"),
#             ("REJECTED", "Rejected"),
#         ],
#         default="PUBLISHED"
#     )

#     created_at = models.DateTimeField(auto_now_add=True)

class Confession(models.Model):

    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"

    CONFESSION_TYPES = (
        (TEXT, "Text"),
        (IMAGE, "Image"),
        (AUDIO, "Audio"),
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="confessions"
    )

    content = models.TextField(
        blank=True
    )

    confession_type = models.CharField(
        max_length=10,
        choices=CONFESSION_TYPES,
        default=TEXT,
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ("PUBLISHED", "Published"),
            ("PENDING", "Pending"),
            ("HIDDEN", "Hidden"),
            ("REJECTED", "Rejected"),
        ],
        default="PUBLISHED"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

class SecretSend(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="secret_sends",
    )

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_secret_sends",
    )

    confession = models.ForeignKey(
        Confession,
        on_delete=models.CASCADE,
        related_name="secret_sends",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Secret send #{self.pk}"


class Reaction(models.Model):

    RELATABLE = "RELATABLE"
    FUNNY = "FUNNY"
    LIKE = "LIKE"
    LOVE = "LOVE"
    WOW = "WOW"
    SAD = "SAD"
    ANGRY = "ANGRY"

    REACTION_CHOICES = (
        (RELATABLE, "Relatable"),
        (FUNNY, "Funny"),
        (LIKE, "Like"),
        (LOVE, "Love"),
        (WOW, "Wow"),
        (SAD, "Sad"),
        (ANGRY, "Angry"),
    )

    confession = models.ForeignKey(
        Confession,
        on_delete=models.CASCADE,
        related_name="reactions"
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="confession_reactions"
    )

    reaction_type = models.CharField(
        max_length=20,
        choices=REACTION_CHOICES
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["confession", "user"],
                name="unique_user_confession_reaction"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.reaction_type}"


class Comment(models.Model):
    confession = models.ForeignKey(
        Confession,
        on_delete=models.CASCADE,
        related_name="comments"
    )

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="confession_comments"
    )

    anonymous_name = models.CharField(
        max_length=50
    )

    content = models.TextField()

    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.anonymous_name}: {self.content[:50]}"


class Report(models.Model):

    REASON_CHOICES = (
        ("SPAM", "Spam"),
        ("HARASSMENT", "Harassment"),
        ("INAPPROPRIATE", "Inappropriate Content"),
        ("BULLYING", "Bullying"),
        ("OTHER", "Other"),
    )

    confession = models.ForeignKey(
        Confession,
        on_delete=models.CASCADE,
        related_name="reports"
    )

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="confession_reports"
    )

    reason = models.CharField(
        max_length=30,
        choices=REASON_CHOICES
    )

    details = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    is_resolved = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report #{self.id}"

class Notification(models.Model):
    REACTION = "REACTION"
    COMMENT = "COMMENT"
    SECRET = "SECRET"

    NOTIFICATION_TYPES = (
        (REACTION, "Reaction"),
        (COMMENT, "Comment"),
        (SECRET, "Secret confession"),
    )

    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    actor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_notifications",
    )

    confession = models.ForeignKey(
        Confession,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
    )

    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

class Report(models.Model):

    HARASSMENT = "HARASSMENT"
    BULLYING = "BULLYING"
    SPAM = "SPAM"
    INAPPROPRIATE = "INAPPROPRIATE"
    THREAT = "THREAT"
    OTHER = "OTHER"

    REASON_CHOICES = (
        (HARASSMENT, "Harassment"),
        (BULLYING, "Bullying"),
        (SPAM, "Spam"),
        (INAPPROPRIATE, "Inappropriate content"),
        (THREAT, "Threat"),
        (OTHER, "Other"),
    )

    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    DISMISSED = "DISMISSED"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (REVIEWED, "Reviewed"),
        (DISMISSED, "Dismissed"),
    )

    confession = models.ForeignKey(
        Confession,
        on_delete=models.CASCADE,
        related_name="reports",
    )

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="confession_reports",
    )

    reason = models.CharField(
        max_length=30,
        choices=REASON_CHOICES,
    )

    description = models.TextField(
        blank=True,
        max_length=500,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=PENDING,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report #{self.id} - Confession #{self.confession_id}"

import uuid
from django.db import models


def confession_media_upload_path(instance, filename):
    extension = filename.split(".")[-1].lower()

    return (
        f"confessions/{uuid.uuid4().hex}.{extension}"
    )


class ConfessionMedia(models.Model):

    IMAGE = "IMAGE"
    AUDIO = "AUDIO"

    MEDIA_TYPES = (
        (IMAGE, "Image"),
        (AUDIO, "Audio"),
    )

    confession = models.ForeignKey(
        Confession,
        on_delete=models.CASCADE,
        related_name="media"
    )

    media_type = models.CharField(
        max_length=10,
        choices=MEDIA_TYPES
    )

    file = models.FileField(
        upload_to=confession_media_upload_path
    )

    mime_type = models.CharField(
        max_length=100
    )

    file_size = models.PositiveBigIntegerField()

    duration = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.media_type} - {self.confession_id}"