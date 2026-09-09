from django.contrib import admin
from .models import Conversation, Message, MessageToolCall


class MessageToolCallInline(admin.TabularInline):
    model = MessageToolCall
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "conversation",
        "role",
        "has_tool_calls",
        "created_at",
    )
    list_filter = (
        "role",
        "has_tool_calls",
        "created_at",
    )
    search_fields = (
        "content",
        "conversation__title",
        "conversation__user__username",
    )
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)

    inlines = [MessageToolCallInline]


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("created_at",)
    fields = (
        "role",
        "content",
        "has_tool_calls",
        "created_at",
    )
    show_change_link = True


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "user",
        "created_at",
        "updated_at",
    )
    list_filter = (
        "created_at",
        "updated_at",
    )
    search_fields = (
        "title",
        "user__username",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    ordering = ("-updated_at",)

    inlines = [MessageInline]


@admin.register(MessageToolCall)
class MessageToolCallAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tool_name",
        "message",
        "tool_call_id",
        "created_at",
    )
    list_filter = (
        "tool_name",
        "created_at",
    )
    search_fields = (
        "tool_name",
        "tool_call_id",
        "message__content",
    )
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)