from rest_framework import serializers
from .models import SystemConfiguration, UserPreference, LLMProviderCredential


class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = [
            "id",
            "theme",
            "font_size",
            "font_family",
            "language",
            "timezone",
            "active_credential",
            "updated_at",
        ]
        read_only_fields = ["id", "updated_at"]


class LLMProviderCredentialSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = LLMProviderCredential
        fields = [
            "id",
            "name",
            "provider_type",
            "scope",
            "model",
            "temperature",
            "max_tokens",
            "base_url",
            "api_key",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def create(self, validated_data):
        api_key = validated_data.pop("api_key", "")
        instance = super().create(validated_data)
        instance.set_api_key(api_key)
        instance.save(update_fields=["api_key_encrypted"])
        return instance

    def update(self, instance, validated_data):
        api_key = validated_data.pop("api_key", None)
        instance = super().update(instance, validated_data)
        if api_key is not None:
            instance.set_api_key(api_key)
            instance.save(update_fields=["api_key_encrypted"])
        return instance


class SystemConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfiguration
        fields = [
            "id",
            "llm_provider",
            "model_name",
            "context_window",
            "temperature",
            "target_db_path",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "updated_at",
        ]