# Universal DB Agent

> Chat with your SQL databases in natural language. A LangChain-powered agent that inspects SQLite databases, answers questions, and generates Markdown / CSV / Excel reports — through a web app or a CLI.

## Features

- **Natural-language database queries** — the agent translates questions into read-only SQL and executes them safely.
- **Automatic report generation** — asks the agent for a summary and it writes Markdown, CSV, or Excel files you can preview and download.
- **Provider-agnostic LLM support** — OpenAI, Anthropic, Google Gemini, DeepSeek, xAI (Grok), Mistral, AWS Bedrock, Hugging Face, OpenRouter, and local models via Ollama.
- **Encrypted credential management** — per-user and per-group LLM credentials (API keys encrypted at rest with Fernet), with an "active model" switcher per user.
- **User preferences** — theme, font, language, timezone, and active credential, persisted per account.
- **Chat history** — conversations and tool calls stored server-side; resume any conversation.
- **Web UI + CLI** — full React SPA or a lightweight REPL (`main.py`) for terminal use.

## Architecture

```
┌────────────────────────────┐      ┌──────────────────────────────────────────┐
│  React SPA (Vite+Tailwind) │      │  Django REST backend (port 8765)         │
│  Chat · Login · Settings   │ ───► │  chat app: conversations, messages,      │
└────────────────────────────┘      │            agent loop, file endpoints    │
                                    │  settings_panel: credentials, prefs,     │
┌────────────────────────────┐      │            system configuration          │
│  CLI: python main.py       │ ───► │  JWT auth (simplejwt) · SQLite storage   │
└────────────────────────────┘      └──────────────────────────────────────────┘
                                                │
                                    ┌───────────▼───────────┐
                                    │  LangChain agent loop  │
                                    │  tools: query_db,      │
                                    │  save_report (.md),    │
                                    │  save_csv, save_excel  │
                                    └───────────┬───────────┘
                                                │
                                    LLM provider of your choice
                                    (OpenAI · Anthropic · Gemini · Ollama · …)
```

### Project layout

```
backend/                 Django project (apps: chat, settings_panel)
  chat/                  agent loop, LangChain tools, conversation models & APIs
  settings_panel/        LLM credentials (encrypted), user preferences, system config
frontend/                React + Vite + Tailwind single-page app
example/setup_db.py      generates a demo SQLite database (construction company)
main.py                  CLI entry point (REPL over the same agent)
docs/                    planning / design notes
storage/                 runtime: database files, exports, reports (gitignored)
```

## Tech stack

| Layer      | Tech |
|------------|------|
| Backend    | Python · Django 6 · Django REST Framework · SimpleJWT · LangChain |
| Frontend   | React 19 · Vite · Tailwind CSS 4 · Axios · React Router |
| Database   | SQLite (app data + the databases being queried) |
| Auth       | JWT access/refresh tokens |
| Crypto     | Fernet (symmetric encryption of stored API keys) |

## Getting started

### 1. Backend

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd backend
python manage.py migrate
python manage.py runserver 8765
```

The API (and the chat UI at `http://localhost:8765/chat/`) is served on port 8765. Create a superuser with `python manage.py createsuperuser` to log in and open the admin at `http://localhost:8765/admin/`.

### 2. Frontend (dev server)

```bash
cd frontend
npm install
npm run dev
```

Vite runs on `http://localhost:5173` and proxies `/api` and `/settings` to the backend.

### 3. CLI (optional)

```bash
source venv/bin/activate
python main.py
```

### 4. Demo database

```bash
python example/setup_db.py      # creates construction_company.db (projects, workers, …)
```

You can then ask things like *"What projects are in progress and what is their total budget?"* or *"Generate a CSV report of workers sorted by hourly rate."*

## Configuration

Copy `.env.example` to `.env` and fill in the keys you need:

| Variable             | Purpose                                   |
|----------------------|-------------------------------------------|
| `GEMINI_API_KEY`     | Used when the provider is Google Gemini   |
| `LANGCHAIN_API_KEY`  | Optional LangSmith tracing                |
| `LANGCHAIN_PROJECT`  | Optional LangSmith project name           |
| `LANGCHAIN_TRACING_V2` | Optional LangSmith tracing toggle       |

Alternatively, manage credentials from the web UI (Settings → Models), where API keys are stored encrypted and can be shared per user or per group, and pick the active model per account.

## API overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/token/` | Obtain JWT (access + refresh) |
| POST | `/api/token/refresh/` | Refresh access token |
| GET/POST | `/api/conversations/` | List / create conversations |
| GET/DELETE | `/api/conversations/<id>/` | Conversation detail |
| POST | `/api/conversations/<id>/messages/` | Send a message to the agent |
| GET | `/api/reports/<filename>/` | View a generated Markdown report |
| GET | `/api/exports/<filename>/` | View a CSV export |
| GET | `/api/files/<id>/download/` · `/preview/` | Download / preview saved files |
| CRUD | `/settings/api/credentials/` | Manage LLM credentials (encrypted) |
| GET/PUT | `/settings/api/preferences/` | User preferences (theme, active model, …) |

## Development notes

- Agent logic and tools live in `backend/chat/agent.py` and `backend/chat/tools.py`.
- Database metadata (table/column descriptions used for prompting) lives in `backend/chat/metadata.json`.
- The `.superpowers/` and `reports/`, `storage/` directories are workspace-local and gitignored.

---

Built with Python, Django, React, and LangChain.
