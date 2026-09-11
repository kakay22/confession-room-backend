from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User

from .models import (
    Confession,
    ConfessionMedia,
    Reaction,
    Comment,
    Notification,
    Report,
    SecretSend,
)

class ConfessionMediaSerializer(serializers.ModelSerializer):

    url = serializers.SerializerMethodField()

    class Meta:
        model = ConfessionMedia

        fields = [
            "id",
            "media_type",
            "url",
            "mime_type",
            "file_size",
            "duration",
            "created_at",
        ]

        read_only_fields = fields

    def get_url(self, obj):

        if not obj.file:
            return None

        request = self.context.get("request")

        url = obj.file.url

        if request:
            return request.build_absolute_uri(url)

        return url


class ConfessionSerializer(serializers.ModelSerializer):

    anonymous_username = serializers.SerializerMethodField()
    anonymous_avatar = serializers.SerializerMethodField()

    reaction_counts = serializers.SerializerMethodField()
    total_reactions = serializers.SerializerMethodField()
    my_reaction = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()

    media = ConfessionMediaSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Confession

        fields = [
            "id",
            "anonymous_username",
            "anonymous_avatar",
            "content",
            "confession_type",
            "status",
            "created_at",

            "media",

            "reaction_counts",
            "total_reactions",
            "my_reaction",
            "comment_count",
        ]

        read_only_fields = [
            "id",
            "anonymous_username",
            "anonymous_avatar",
            "status",
            "created_at",
            "media",
            "reaction_counts",
            "total_reactions",
            "my_reaction",
            "comment_count",
        ]

    def validate_content(self, value):
        value = value.strip()

        if len(value) > 2000:
            raise serializers.ValidationError(
                "Confession cannot exceed 2000 characters."
            )

        return value

    def validate(self, attrs):

        confession_type = attrs.get(
            "confession_type",
            Confession.TEXT
        )

        content = attrs.get("content", "").strip()

        if confession_type == Confession.TEXT and not content:
            raise serializers.ValidationError({
                "content": "Text confession cannot be empty."
            })

        if confession_type in [
            Confession.IMAGE,
            Confession.AUDIO
        ] and not content:
            raise serializers.ValidationError({
                "content": "Please add a caption."
            })

        return attrs

    def get_anonymous_username(self, obj):
        try:
            return obj.author.profile.anonymous_username
        except AttributeError:
            return "Anonymous"

    def get_anonymous_avatar(self, obj):
        try:
            return obj.author.profile.anonymous_avatar
        except AttributeError:
            return "avatar1"

    def get_reaction_counts(self, obj):
        counts = {}

        for reaction_type, label in Reaction.REACTION_CHOICES:
            counts[reaction_type] = obj.reactions.filter(
                reaction_type=reaction_type
            ).count()

        return counts

    def get_total_reactions(self, obj):
        return obj.reactions.count()

    def get_my_reaction(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return None

        reaction = obj.reactions.filter(
            user=request.user
        ).first()

        return reaction.reaction_type if reaction else None

    def get_comment_count(self, obj):
        return obj.comments.count()


class ReactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Reaction

        fields = [
            "id",
            "confession",
            "reaction_type",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "confession",
            "created_at",
        ]

    def validate_reaction_type(self, value):

        valid_types = dict(
            Reaction.REACTION_CHOICES
        ).keys()

        if value not in valid_types:
            raise serializers.ValidationError(
                "Invalid reaction type."
            )

        return value


class CommentSerializer(serializers.ModelSerializer):
    anonymous_username = serializers.SerializerMethodField()
    anonymous_avatar = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "confession",
            "parent",
            "anonymous_username",
            "anonymous_avatar",
            "content",
            "created_at",
            "replies",
        ]

        read_only_fields = [
            "id",
            "confession",
            "anonymous_username",
            "anonymous_avatar",
            "created_at",
            "replies",
        ]

    def get_anonymous_username(self, obj):
        try:
            return obj.author.profile.anonymous_username
        except AttributeError:
            return "Anonymous"

    def get_anonymous_avatar(self, obj):
        try:
            return obj.author.profile.anonymous_avatar
        except AttributeError:
            return "avatar1"

    def get_replies(self, obj):
        replies = obj.replies.all()

        return CommentSerializer(
            replies,
            many=True,
            context=self.context
        ).data

class NotificationSerializer(serializers.ModelSerializer):

    anonymous_username = serializers.SerializerMethodField()

    confession_content = serializers.CharField(
        source="confession.content",
        read_only=True,
    )

    class Meta:
        model = Notification

        fields = [
            "id",
            "notification_type",
            "confession",
            "confession_content",
            "anonymous_username",
            "is_read",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "notification_type",
            "confession",
            "confession_content",
            "anonymous_username",
            "created_at",
        ]

    def get_anonymous_username(self, obj):
        try:
            return obj.actor.profile.anonymous_username
        except AttributeError:
            return "Anonymous"

class ReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = Report
        fields = [
            "id",
            "confession",
            "reason",
            "description",
            "status",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "confession",
            "status",
            "created_at",
        ]

    def validate_description(self, value):
        return value.strip()

class SecretRecipientSerializer(serializers.ModelSerializer):

    anonymous_username = serializers.CharField(
        source="profile.anonymous_username",
        read_only=True
    )

    anonymous_avatar = serializers.CharField(
        source="profile.anonymous_avatar",
        read_only=True
    )

    class Meta:
        model = User

        fields = [
            "id",
            "anonymous_username",
            "anonymous_avatar",
        ]

        read_only_fields = fields


class SecretSendSerializer(serializers.ModelSerializer):

    recipient_username = serializers.CharField(
        source="recipient.profile.anonymous_username",
        read_only=True
    )

    class Meta:
        model = SecretSend

        fields = [
            "id",
            "confession",
            "recipient",
            "recipient_username",
            "created_at",
            "is_read",
        ]

        read_only_fields = [
            "id",
            "recipient_username",
            "created_at",
            "is_read",
        ]