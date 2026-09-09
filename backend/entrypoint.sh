#!/bin/sh
set -e

DATA_DIR="${DATA_DIR:-/app/data}"
export DATA_DIR

# 1. Ensure writable data directories exist
mkdir -p "$DATA_DIR/reports/markdown" "$DATA_DIR/reports/csv" "$DATA_DIR/reports/excel" "$DATA_DIR/exports" "$DATA_DIR/storage/config"

# 2. Persistent SECRET_KEY (generated once, reused across restarts)
if [ -f "$DATA_DIR/.secret_key" ]; then
    SECRET_KEY="$(cat "$DATA_DIR/.secret_key")"
else
    if [ -z "$SECRET_KEY" ]; then
        SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')"
    fi
    printf '%s' "$SECRET_KEY" > "$DATA_DIR/.secret_key"
fi
export SECRET_KEY

cd /app/backend

# 3. Apply database migrations
python manage.py migrate --noinput

# 4. Seed the demo database if it does not exist yet
if [ ! -f "$DATA_DIR/construction_company.db" ]; then
    (cd "$DATA_DIR" && python /app/example/setup_db.py)
fi

# 5-7. Idempotent seeding: superuser, SystemConfiguration, active LLM credential
python manage.py shell <<'PYEOF'
import os
import sys
from django.contrib.auth import get_user_model

try:
    User = get_user_model()
    data_dir = os.environ.get("DATA_DIR", "/app/data")

    # 5. Superuser (non-interactive, never prompts)
    username = os.environ.get("ADMIN_USERNAME") or ""
    password = os.environ.get("ADMIN_PASSWORD") or ""
    admin = None
    if username and password:
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email="", password=password)
        admin = User.objects.filter(username=username).first()
    if admin is None:
        admin = User.objects.filter(is_superuser=True).order_by("id").first()

    # 6. SystemConfiguration singleton -> absolute demo DB path
    from settings_panel.models import SystemConfiguration
    cfg = SystemConfiguration.get_solo()
    target_db = os.path.join(data_dir, "construction_company.db")
    if cfg.target_db_path != target_db:
        cfg.target_db_path = target_db
        cfg.save(update_fields=["target_db_path"])

    # 7. Effective LLM provider + active credential (mirror UI activate_credential flow)
    provider = (os.environ.get("LLM_PROVIDER") or "").strip().lower() or None
    gemini_key = os.environ.get("GEMINI_API_KEY") or ""
    ollama_base = os.environ.get("OLLAMA_BASE_URL") or ""
    if not provider:
        provider = "google" if gemini_key else "ollama"

    if admin is not None:
        from settings_panel.models import LLMProviderCredential, UserPreference

        if provider == "google" and gemini_key:
            model = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
            cred = LLMProviderCredential.objects.filter(user=admin, provider_type="google").first()
            if cred:
                cred.model = model
                cred.base_url = ""
                cred.set_api_key(gemini_key)
                cred.save()
            else:
                cred = LLMProviderCredential.objects.create(
                    name="Google Gemini (Auto)",
                    provider_type="google",
                    scope="personal",
                    user=admin,
                    model=model,
                    temperature=0.0,
                    max_tokens=4096,
                    base_url="",
                )
                cred.set_api_key(gemini_key)
                cred.save(update_fields=["api_key_encrypted"])
            pref, _ = UserPreference.objects.get_or_create(user=admin)
            pref.active_credential = cred
            pref.save(update_fields=["active_credential"])

        elif provider == "ollama" and ollama_base:
            model = os.environ.get("OLLAMA_MODEL") or "gemma4:latest"
            cred = LLMProviderCredential.objects.filter(user=admin, provider_type="ollama").first()
            if cred:
                cred.model = model
                cred.base_url = ollama_base
                cred.set_api_key("")
                cred.save()
            else:
                cred = LLMProviderCredential.objects.create(
                    name="Ollama (Auto)",
                    provider_type="ollama",
                    scope="personal",
                    user=admin,
                    model=model,
                    temperature=0.0,
                    max_tokens=4096,
                    base_url=ollama_base,
                )
            pref, _ = UserPreference.objects.get_or_create(user=admin)
            pref.active_credential = cred
            pref.save(update_fields=["active_credential"])
except Exception:
    import traceback
    traceback.print_exc()
    sys.exit(1)
PYEOF

exec "$@"
