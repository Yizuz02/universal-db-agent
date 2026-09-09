import shutil
import subprocess

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserPreference, LLMProviderCredential, ensure_default_credential
from .serializers import UserPreferenceSerializer, LLMProviderCredentialSerializer


def get_ollama_models():
    """
    Runs `ollama list` on the server and returns the installed models.
    Returns [] if ollama is not installed or the command fails.
    """
    if shutil.which("ollama") is None:
        return []
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            return []
        lines = result.stdout.strip().splitlines()
        models = []
        for line in lines[1:]:  # skip the header row
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models
    except Exception:
        return []


class UserPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ensure_default_credential(request.user)
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(pref)
        return Response(serializer.data)

    def put(self, request):
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        serializer = UserPreferenceSerializer(pref, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def credential_list(request):
    if request.method == "GET":
        ensure_default_credential(request.user)
        creds = LLMProviderCredential.objects.filter(
            user=request.user
        ) | LLMProviderCredential.objects.filter(
            group__in=request.user.groups.all()
        )
        creds = creds.order_by("-created_at")
        serializer = LLMProviderCredentialSerializer(creds, many=True)
        data = serializer.data
        # Annotate which credential is active for this user
        pref, _ = UserPreference.objects.get_or_create(user=request.user)
        active_id = pref.active_credential_id
        for item in data:
            item["is_active"] = item["id"] == active_id
        return Response(data)

    elif request.method == "POST":
        data = request.data.copy()
        # Personal credentials belong to the requesting user
        if data.get("scope") == "personal":
            data["user"] = request.user.id
            data.pop("group", None)
        # Group credentials: must belong to a group the user is a member of
        else:
            data.pop("user", None)
            group_id = data.get("group")
            if group_id and not request.user.groups.filter(pk=group_id).exists():
                return Response({"error": "Not a member of that group"}, status=status.HTTP_403_FORBIDDEN)
        serializer = LLMProviderCredentialSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def credential_detail(request, pk):
    try:
        cred = LLMProviderCredential.objects.get(pk=pk)
    except LLMProviderCredential.DoesNotExist:
        return Response({"error": "Not found"}, status=status.HTTP_404_NOT_FOUND)

    # Only allow owner or group member to modify
    if cred.scope == "personal" and cred.user != request.user:
        return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)
    if cred.scope == "group" and not request.user.groups.filter(pk=cred.group_id).exists():
        return Response({"error": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PUT":
        data = request.data.copy()
        data.pop("user", None)
        if cred.scope == "personal":
            data["user"] = request.user.id
        serializer = LLMProviderCredentialSerializer(cred, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        cred.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
def activate_credential(request):
    pref, _ = UserPreference.objects.get_or_create(user=request.user)
    cred_id = request.data.get("credential_id")
    if cred_id is None:
        pref.active_credential = None
        pref.save()
        return Response({"active_credential": None})
    try:
        cred = LLMProviderCredential.objects.get(pk=cred_id)
    except LLMProviderCredential.DoesNotExist:
        return Response({"error": "Not found"}, status=404)
    pref.active_credential = cred
    pref.save()
    return Response({"active_credential": cred_id})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def provider_options(request):
    return Response({
        "providers": [
            {"id": "openai", "name": "OpenAI", "has_base_url": False, "has_api_key": True, "default_base_url": "",
             "models": ["gpt-5.6-luna-pro", "gpt-5.6-luna", "gpt-5.6-terra-pro", "gpt-5.6-terra", "gpt-4o", "gpt-4o-mini"]},
            {"id": "anthropic", "name": "Anthropic", "has_base_url": False, "has_api_key": True, "default_base_url": "",
             "models": ["claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5", "claude-mythos-5", "claude-fable-5"]},
            {"id": "google", "name": "Google Gemini", "has_base_url": False, "has_api_key": True, "default_base_url": "",
             "models": ["gemini-3.6-flash", "gemini-3.1-pro-preview", "gemini-3-pro-image", "gemini-2.5-pro", "gemini-2.5-flash"]},
            {"id": "ollama", "name": "Ollama", "has_base_url": True, "has_api_key": False, "default_base_url": "http://localhost:11434",
              "models": get_ollama_models() or ["gemma4:latest", "qwen3.6:35b", "qwen3.5:4b", "qwen3-coder:30b", "llama4-maverick:latest", "mistral:latest", "phi4:latest"]},
            {"id": "xai", "name": "Grok (xAI)", "has_base_url": False, "has_api_key": True, "default_base_url": "",
             "models": ["grok-4.5", "grok-4.3", "grok-4.20-multi-agent", "grok-3"]},
            {"id": "mistral", "name": "Mistral", "has_base_url": False, "has_api_key": True, "default_base_url": "",
             "models": ["mistral-medium-2508", "mistral-small-2603", "mistral-small-2506", "ministral-14b-2512", "ministral-8b-2512"]},
            {"id": "bedrock", "name": "AWS Bedrock", "has_base_url": False, "has_api_key": False, "default_base_url": "",
             "models": ["anthropic.claude-sonnet-5", "anthropic.claude-opus-5", "meta.llama4-maverick-17b-128e-instruct-v1:0", "amazon.nova-2-pro-v1:0", "amazon.nova-2-lite-v1:0"]},
            {"id": "huggingface", "name": "Hugging Face", "has_base_url": False, "has_api_key": True, "default_base_url": "",
             "models": ["meta-llama/Llama-4-Maverick-17B-128E-Instruct", "meta-llama/Llama-4-Scout-17B-16E-Instruct", "google/gemma-4-31B-it", "google/gemma-4-12B-it", "mistralai/Mistral-Small-3.2-24B-Instruct-2506"]},
            {"id": "openrouter", "name": "OpenRouter", "has_base_url": False, "has_api_key": True, "default_base_url": "",
             "models": ["anthropic/claude-sonnet-5", "anthropic/claude-opus-5", "openai/gpt-5.6-luna-pro", "google/gemini-3.6-flash", "x-ai/grok-4.5", "deepseek/deepseek-v4-pro", "deepseek/deepseek-v4-flash", "meta-llama/llama-4-maverick", "meta-llama/llama-4-scout"]},
            {"id": "deepseek", "name": "DeepSeek", "has_base_url": False, "has_api_key": True, "default_base_url": "",
             "models": ["deepseek-v4-pro", "deepseek-v4-flash", "deepseek-v4-flash-0731", "deepseek-v3.2"]},
        ],
        "groups": [{"id": g.id, "name": g.name} for g in request.user.groups.all()],
    })
