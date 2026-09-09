from rest_framework import serializers
from .models import Conversation, Message, MessageToolCall, GeneratedFile

class GeneratedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedFile
        fields = ['id', 'filename', 'extension', 'size_bytes', 'created_at']
        read_only_fields = ['id', 'created_at']

class MessageToolCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageToolCall
        fields = [
            "id",
            "tool_name",
            "tool_args",
            "tool_output",
            "tool_call_id",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    tool_calls = MessageToolCallSerializer(many=True, read_only=True)
    files = GeneratedFileSerializer(source='generated_files', many=True, read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "role",
            "content",
            "has_tool_calls",
            "tool_calls",
            "files",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = [
            "id",
            "user",
            "title",
            "title_edited",
            "messages",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "title_edited"]


class ConversationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = ["id", "title", "title_edited", "created_at", "updated_at"]
        read_only_fields = ["id", "title_edited", "created_at", "updated_at"]


class MessageInputSerializer(serializers.Serializer):
    content = serializers.CharField(
        max_length=10000,
        trim_whitespace=True
    )

    def validate_content(self, value):
        value = value.strip()

        if not value:
            raise serializers.ValidationError("Message content cannot be empty.")

        return value

class TitleUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(
        max_length=255,
        trim_whitespace=True
    )

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be empty.")
        return value