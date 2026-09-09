from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.models import Group
import base64
import hashlib
from cryptography.fernet import Fernet


def get_fernet():
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


class LLMProviderCredential(models.Model):
    PROVIDER_CHOICES = [
        ("openai", "OpenAI"),
        ("anthropic", "Anthropic"),
        ("google", "Google Gemini"),
        ("ollama", "Ollama"),
        ("xai", "Grok (xAI)"),
        ("mistral", "Mistral"),
        ("bedrock", "AWS Bedrock"),
        ("huggingface", "Hugging Face"),
        ("openrouter", "OpenRouter"),
        ("deepseek", "DeepSeek"),
    ]
    SCOPE_CHOICES = [
        ("personal", "Personal"),
        ("group", "Group"),
    ]

    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="llm_credentials",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="llm_credentials",
    )
    api_key_encrypted = models.TextField(blank=True, default="")
    model = models.CharField(max_length=100, default="gpt-4o")
    temperature = models.FloatField(default=0.0)
    max_tokens = models.IntegerField(default=4096)
    base_url = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_api_key(self, raw_key):
        if not raw_key:
            self.api_key_encrypted = ""
            return
        self.api_key_encrypted = get_fernet().encrypt(raw_key.encode()).decode()

    def get_api_key(self):
        if not self.api_key_encrypted:
            return ""
        return get_fernet().decrypt(self.api_key_encrypted.encode()).decode()

    class Meta:
        verbose_name = "LLM Credential"
        verbose_name_plural = "LLM Credentials"

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"


# ---------------------------------------------------------------------------
# Default credential helpers
# ---------------------------------------------------------------------------

DEFAULT_OLLAMA_MODEL = "gemma4:latest"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"


def ensure_default_credential(user):
    """
    Creates the default Ollama credential for a user if they have none yet
    (matches the agent's SystemConfiguration default: ollama + gemma4:latest).
    Returns the credential, or None if the user already had credentials.
    """
    if user.llm_credentials.exists():
        return None

    cred = LLMProviderCredential.objects.create(
        name="Ollama (Default)",
        provider_type="ollama",
        scope="personal",
        user=user,
        model=DEFAULT_OLLAMA_MODEL,
        temperature=0.0,
        max_tokens=4096,
        base_url=DEFAULT_OLLAMA_BASE_URL,
    )

    # Make it the active credential for this user
    pref, _ = UserPreference.objects.get_or_create(user=user)
    if pref.active_credential is None:
        pref.active_credential = cred
        pref.save(update_fields=["active_credential"])

    return cred


class UserPreference(models.Model):
    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
        ("ocean", "Ocean"),
        ("matrix", "Matrix"),
        ("sunset", "Sunset"),
        ("blush", "Blush"),
        ("synthwave", "Synthwave"),
        ("graphite", "Graphite"),
    ]

    FONT_SIZE_CHOICES = [
        ("12px", "12px"),
        ("14px", "14px"),
        ("16px", "16px"),
        ("18px", "18px"),
    ]

    FONT_FAMILY_CHOICES = [
        ("system", "System UI"),
        ("serif", "Serif"),
        ("mono", "Monospace"),
        ("rounded", "Rounded"),
    ]

    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("es", "Español"),
    ]

    TIMEZONE_CHOICES = [
        ("America/Mexico_City", "CDMX (UTC-6)"),
        ("America/New_York", "New York (UTC-5)"),
        ("America/Chicago", "Chicago (UTC-6)"),
        ("America/Denver", "Denver (UTC-7)"),
        ("America/Los_Angeles", "Los Angeles (UTC-8)"),
        ("America/Argentina/Buenos_Aires", "Buenos Aires (UTC-3)"),
        ("America/Sao_Paulo", "São Paulo (UTC-3)"),
        ("Europe/Madrid", "Madrid (UTC+1)"),
        ("Europe/London", "London (UTC+0)"),
        ("Europe/Berlin", "Berlin (UTC+1)"),
        ("Asia/Tokyo", "Tokyo (UTC+9)"),
        ("Asia/Shanghai", "Shanghai (UTC+8)"),
        ("Asia/Kolkata", "India (UTC+5:30)"),
        ("Australia/Sydney", "Sydney (UTC+10)"),
        ("Pacific/Auckland", "Auckland (UTC+12)"),
        ("UTC", "UTC"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="preferences",
    )
    theme = models.CharField(
        max_length=20,
        choices=THEME_CHOICES,
        default="light",
    )
    font_size = models.CharField(
        max_length=4,
        choices=FONT_SIZE_CHOICES,
        default="16px",
    )
    font_family = models.CharField(
        max_length=10,
        choices=FONT_FAMILY_CHOICES,
        default="system",
    )
    language = models.CharField(
        max_length=10,
        choices=LANGUAGE_CHOICES,
        default="en",
    )
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default="America/Mexico_City",
    )
    active_credential = models.ForeignKey(
        LLMProviderCredential,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="active_for_users",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Preference"
        verbose_name_plural = "User Preferences"

    def __str__(self):
        return f"{self.user.username} — {self.get_theme_display()}"


class SystemConfiguration(models.Model):
    PROVIDER_CHOICES = [
        ('ollama', 'Ollama (Local)'),
        ('google', 'Google Gemini'),
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('xai', 'Grok (xAI)'),
        ('mistral', 'Mistral'),
        ('bedrock', 'AWS Bedrock'),
        ('huggingface', 'Hugging Face'),
        ('openrouter', 'OpenRouter'),
        ('deepseek', 'DeepSeek'),
    ]

    # 1. LLM Core Configurations
    llm_provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='ollama')
    model_name = models.CharField(max_length=100, default='gemma4:latest', help_text="Exact model tag/name.")
    context_window = models.IntegerField(default=8192, help_text="Context window size (num_ctx).")
    temperature = models.FloatField(default=0.0, help_text="Model creativity level (0 = deterministic).")

    # 2. Database Target Configurations
    target_db_path = models.CharField(
        max_length=500, 
        default="storage/databases/construction_company.db",
        help_text="Local absolute or relative path to the target SQLite database to inspect."
    )

    # 3. System Metadata
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "System Configuration"
        verbose_name_plural = "System Configuration"

    # --- SINGLETON GUARDRAIL ---
    def clean(self):
        """Prevents creating more than one configuration record in the DB."""
        if SystemConfiguration.objects.exists() and not self.pk:
            raise ValidationError("Only one active SystemConfiguration instance is allowed.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls):
        """Helper method to easily fetch the active config or create a default one if empty."""
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return f"Active Config: {self.llm_provider.upper()} - {self.model_name}"