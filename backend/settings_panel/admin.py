from django.contrib import admin
from .models import SystemConfiguration, UserPreference


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "llm_provider",
        "model_name",
        "context_window",
        "temperature",
        "updated_at",
    )

    readonly_fields = ("updated_at",)

    fieldsets = (
        (
            "LLM Configuration",
            {
                "fields": (
                    "llm_provider",
                    "model_name",
                    "context_window",
                    "temperature",
                )
            },
        ),
        (
            "Database Configuration",
            {
                "fields": ("target_db_path",)
            },
        ),
        (
            "Metadata",
            {
                "fields": ("updated_at",)
            },
        ),
    )

    def has_add_permission(self, request):
        # Solo permite crear la configuración si aún no existe.
        return not SystemConfiguration.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Evita eliminar la configuración activa.
        return False


@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "theme", "updated_at")
    list_filter = ("theme",)
    search_fields = ("user__username",)