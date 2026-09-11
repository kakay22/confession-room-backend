from django.contrib import admin
from .models import Confession, Reaction, Comment, Report


@admin.register(Confession)
class ConfessionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "anonymous_username",
        "content_preview",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "content",
        "author__username",
        "author__profile__anonymous_username",
    )

    def anonymous_username(self, obj):
        return obj.author.profile.anonymous_username

    anonymous_username.short_description = "Anonymous Username"

    def content_preview(self, obj):
        return obj.content[:50]

    content_preview.short_description = "Content"


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):

    list_display = (
        "confession",
        "user",
        "reaction_type",
        "created_at",
    )

    list_filter = (
        "reaction_type",
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):

    list_display = (
        "confession",
        "anonymous_name",
        "created_at",
    )


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "confession",
        "reporter",
        "reason",
        "status",
        "created_at",
    )

    list_filter = (
        "reason",
        "status",
        "created_at",
    )

    search_fields = (
        "confession__content",
        "reporter__username",
        "description",
    )

    readonly_fields = (
        "confession",
        "reporter",
        "reason",
        "description",
        "created_at",
        "reviewed_at",
    )

    ordering = (
        "-created_at",
    )