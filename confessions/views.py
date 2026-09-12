from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404
from PIL import Image

from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    UserProfile,
    Confession,
    ConfessionMedia,
    Notification,
    Reaction,
    Comment,
    Report,
    SecretSend,
)

from .serializers import (
    ConfessionSerializer,
    NotificationSerializer,
    ReactionSerializer,
    CommentSerializer,
    ReportSerializer,
    SecretRecipientSerializer,
    SecretSendSerializer,
)


# ============================================================
# CONFESSIONS
# ============================================================

class ConfessionListCreateView(generics.ListCreateAPIView):

    queryset = Confession.objects.all().order_by("-created_at")
    serializer_class = ConfessionSerializer

    parser_classes = [
        JSONParser,
        MultiPartParser,
        FormParser,
    ]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]

        return [AllowAny()]

    def perform_create(self, serializer):

        confession = serializer.save(
            author=self.request.user
        )

        uploaded_file = self.request.FILES.get("media")

        if not uploaded_file:
            return

        # Validate panorama image
        if confession_type == Confession.PANORAMA:

            if not uploaded_file.content_type:
                raise ValidationError(
                    "We couldn't determine the uploaded file type."
                )

            if not uploaded_file.content_type.startswith("image/"):
                raise ValidationError(
                    "A 360° panorama must be an image file."
                )

            try:
                image = Image.open(uploaded_file)
                width, height = image.size

            except Exception:
                raise ValidationError(
                    "The uploaded panorama is not a valid image."
                )

            # Equirectangular panoramas are normally close to a 2:1 ratio.
            ratio = width / height if height else 0

            if ratio < 1.7 or ratio > 2.3:
                raise ValidationError(
                    "This image does not appear to be a 360° panorama. "
                    "Please upload an equirectangular 360° photo."
                )

            # Reset file position after PIL reads it.
            uploaded_file.seek(0)

        confession_type = self.request.data.get(
            "confession_type",
            Confession.TEXT
        )

        # Determine media type
        if confession_type == Confession.IMAGE:
            media_type = ConfessionMedia.IMAGE

        elif confession_type == Confession.AUDIO:
            media_type = ConfessionMedia.AUDIO

        elif confession_type == Confession.PANORAMA:
            media_type = ConfessionMedia.PANORAMA

        else:
            return

        # Get duration for audio
        duration = None

        if media_type == ConfessionMedia.AUDIO:

            duration_value = self.request.data.get(
                "media_duration"
            )

            if duration_value:
                try:
                    duration = int(duration_value)
                except (TypeError, ValueError):
                    duration = None

        ConfessionMedia.objects.create(
            confession=confession,
            media_type=media_type,
            file=uploaded_file,
            mime_type=uploaded_file.content_type or "",
            file_size=uploaded_file.size,
            duration=duration,
        )


class ConfessionDetailView(generics.RetrieveAPIView):

    queryset = Confession.objects.all()
    serializer_class = ConfessionSerializer
    permission_classes = [AllowAny]


# ============================================================
# REACTIONS
# ============================================================

class ReactionCreateView(generics.CreateAPIView):

    queryset = Reaction.objects.all()
    serializer_class = ReactionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        confession_id = self.kwargs["confession_id"]

        reaction_type = request.data.get(
            "reaction_type"
        )

        if not reaction_type:
            return Response(
                {
                    "detail": "Reaction type is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        valid_types = dict(
            Reaction.REACTION_CHOICES
        ).keys()

        if reaction_type not in valid_types:
            return Response(
                {
                    "detail": "Invalid reaction type."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        confession = get_object_or_404(
            Confession,
            id=confession_id,
        )

        existing_reaction = Reaction.objects.filter(
            confession=confession,
            user=request.user,
        ).first()

        # ----------------------------------------------------
        # NO EXISTING REACTION
        # ----------------------------------------------------

        if not existing_reaction:

            reaction = Reaction.objects.create(
                confession=confession,
                user=request.user,
                reaction_type=reaction_type,
            )

            if confession.author != request.user:

                Notification.objects.create(
                    recipient=confession.author,
                    actor=request.user,
                    confession=confession,
                    notification_type=Notification.REACTION,
                )

            serializer = self.get_serializer(reaction)

            return Response(
                {
                    "action": "created",
                    "reaction": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        # ----------------------------------------------------
        # SAME REACTION = REMOVE
        # ----------------------------------------------------

        if existing_reaction.reaction_type == reaction_type:

            existing_reaction.delete()

            return Response(
                {
                    "action": "removed",
                    "reaction_type": reaction_type,
                },
                status=status.HTTP_200_OK,
            )

        # ----------------------------------------------------
        # DIFFERENT REACTION = CHANGE
        # ----------------------------------------------------

        old_reaction = existing_reaction.reaction_type

        existing_reaction.reaction_type = reaction_type

        existing_reaction.save(
            update_fields=["reaction_type"]
        )

        serializer = self.get_serializer(
            existing_reaction
        )

        if confession.author != request.user:

            Notification.objects.create(
                recipient=confession.author,
                actor=request.user,
                confession=confession,
                notification_type=Notification.REACTION,
            )

        return Response(
            {
                "action": "changed",
                "old_reaction": old_reaction,
                "reaction": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# COMMENTS + REPLIES
# ============================================================

class CommentListCreateView(
    generics.ListCreateAPIView
):

    serializer_class = CommentSerializer

    def get_queryset(self):

        confession_id = self.kwargs[
            "confession_id"
        ]

        return Comment.objects.filter(
            confession_id=confession_id
        ).order_by("created_at")

    def get_permissions(self):

        if self.request.method == "POST":
            return [IsAuthenticated()]

        return [AllowAny()]

    def perform_create(self, serializer):

        confession_id = self.kwargs[
            "confession_id"
        ]

        profile = get_object_or_404(
            UserProfile,
            user=self.request.user,
        )

        parent_id = self.request.data.get(
            "parent"
        )

        parent = None

        if parent_id:

            parent = get_object_or_404(
                Comment,
                id=parent_id,
                confession_id=confession_id,
            )

        comment = serializer.save(
            confession_id=confession_id,
            author=self.request.user,
            anonymous_name=profile.anonymous_username,
            parent=parent,
        )

        confession = comment.confession

        if confession.author != self.request.user:

            Notification.objects.create(
                recipient=confession.author,
                actor=self.request.user,
                confession=confession,
                notification_type=Notification.COMMENT,
            )


# ============================================================
# NOTIFICATIONS
# ============================================================

class NotificationListView(generics.ListAPIView):

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return (
            Notification.objects
            .filter(recipient=self.request.user)
            .select_related(
                "confession",
                "actor",
                "actor__profile",
            )
            .order_by("-created_at")
        )


class NotificationMarkReadView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, notification_id):

        notification = get_object_or_404(
            Notification,
            id=notification_id,
            recipient=request.user,
        )

        notification.is_read = True

        notification.save(
            update_fields=["is_read"]
        )

        # Keep SecretSend read state synchronized
        if notification.notification_type == Notification.SECRET:

            SecretSend.objects.filter(
                recipient=request.user,
                confession=notification.confession,
                is_read=False,
            ).update(
                is_read=True
            )

        return Response(
            {
                "success": True
            },
            status=status.HTTP_200_OK,
        )


# ============================================================
# REPORTS
# ============================================================

class ReportCreateView(generics.CreateAPIView):

    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):

        confession_id = self.kwargs[
            "confession_id"
        ]

        confession = get_object_or_404(
            Confession,
            id=confession_id,
        )

        # Prevent users from reporting their own confession
        if confession.author == self.request.user:

            raise ValidationError(
                "You cannot report your own confession."
            )

        # Prevent duplicate pending reports
        existing_report = Report.objects.filter(
            confession=confession,
            reporter=self.request.user,
            status=Report.PENDING,
        ).exists()

        if existing_report:

            raise ValidationError(
                "You have already reported this confession."
            )

        serializer.save(
            confession=confession,
            reporter=self.request.user,
        )


# ============================================================
# SEND SECRETLY
# ============================================================

class SecretRecipientSearchView(
    generics.ListAPIView
):

    serializer_class = SecretRecipientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        queryset = (
            User.objects
            .filter(
                is_active=True,
                profile__isnull=False,
            )
            .exclude(
                id=self.request.user.id
            )
            .select_related("profile")
            .order_by(
                "profile__anonymous_username"
            )
        )

        search = self.request.query_params.get(
            "search",
            ""
        ).strip()

        if search:

            queryset = queryset.filter(
                Q(
                    profile__anonymous_username__icontains=search
                )
            )

        return queryset[:10]


class SecretSendCreateView(
    generics.CreateAPIView
):

    serializer_class = SecretSendSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        confession_id = self.kwargs[
            "confession_id"
        ]

        confession = get_object_or_404(
            Confession,
            id=confession_id,
        )

        # Only published confessions can be sent secretly
        if confession.status != "PUBLISHED":

            return Response(
                {
                    "detail": "This confession cannot be sent secretly."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        recipient_id = request.data.get(
            "recipient"
        )

        if not recipient_id:

            return Response(
                {
                    "detail": "Please select a recipient."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # GET RECIPIENT
        # ----------------------------------------------------

        recipient = get_object_or_404(
            User,
            id=recipient_id,
            is_active=True,
        )

        # ----------------------------------------------------
        # PREVENT SELF-SENDING
        # ----------------------------------------------------

        if recipient == request.user:

            return Response(
                {
                    "detail": "You cannot send a secret to yourself."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # RECIPIENT MUST HAVE AN ANONYMOUS PROFILE
        # ----------------------------------------------------

        try:
            recipient.profile
        except UserProfile.DoesNotExist:

            return Response(
                {
                    "detail": "This user is not available as a recipient."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ----------------------------------------------------
        # BASIC SPAM PROTECTION
        #
        # Same sender + recipient + confession cannot be
        # repeatedly sent within 2 minutes.
        # ----------------------------------------------------

        from django.utils import timezone
        from datetime import timedelta

        recent_limit = (
            timezone.now()
            - timedelta(minutes=2)
        )

        recent_send = SecretSend.objects.filter(
            sender=request.user,
            recipient=recipient,
            confession=confession,
            created_at__gte=recent_limit,
        ).exists()

        if recent_send:

            return Response(
                {
                    "detail": "You recently sent this confession to this person. Please wait a moment."
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # ----------------------------------------------------
        # CREATE SECRET SEND
        # ----------------------------------------------------

        secret_send = SecretSend.objects.create(
            sender=request.user,
            recipient=recipient,
            confession=confession,
        )

        # ----------------------------------------------------
        # CREATE ANONYMOUS NOTIFICATION
        # ----------------------------------------------------

        Notification.objects.create(
            recipient=recipient,
            actor=request.user,
            confession=confession,
            notification_type=Notification.SECRET,
        )

        serializer = self.get_serializer(
            secret_send
        )

        return Response(
            {
                "success": True,
                "message": "Secret confession sent successfully.",
                "secret_send": serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )