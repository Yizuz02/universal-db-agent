# Universal DB Agent Refactoring Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the Universal DB Agent to inject database paths, fix report directory structure, and correct CLI execution, ensuring robustness and adherence to project conventions.

**Architecture:** This plan focuses on centralizing path management, introducing a tool factory for dependency injection, and standardizing report output locations. It will also fix module import issues in the CLI entrypoint.

**Tech Stack:** Python 3.12, Django 6.0.7, SQLite, LangChain, DRF.

## Global Constraints

- Do NOT touch `frontend/`.
- Do NOT modify Django models or create migrations.
- Keep the 5 tool names and descriptions unchanged (`list_tables_and_columns`, `execute_read_only_query`, `save_markdown_report`, `get_current_datetime`, `export_query_to_csv`).
- Python commands must always be run as: `env -u PYTHONPATH ./venv/bin/python ...` from the project root.
- The project root is `/home/yizuz/Documents/Projects/universal-db-agent`.
- The current DB value is an absolute path: `/home/yizuz/Documents/Projects/universal-db-agent/construction_company.db`.

---

### Task 1.1: Refactor `backend/chat/tools.py` for path injection

**Files:**
- Modify: `/home/yizuz/Documents/Projects/universal-db-agent/backend/chat/tools.py`

**Interfaces:**
- Produces: `build_tools(db_path, reports_dir)` factory function that returns the 5 tool functions.

- [ ] **Step 1: Remove module-level path constants.**
    - Delete `DB_PATH`, `REPORTS_DIR`, `EXPORTS_DIR` definitions.

- [ ] **Step 2: Implement `build_tools` factory function.**
    - Define `build_tools(db_path, reports_dir)` which encapsulates the tool definitions.

- [ ] **Step 3: Update `list_tables_and_columns` to use injected `db_path`.**
    - Replace `sqlite3.connect(DB_PATH)` with `sqlite3.connect(db_path)`.

- [ ] **Step 4: Update `execute_read_only_query` to use injected `db_path`.**
    - Replace `sqlite3.connect(DB_PATH)` with `sqlite3.connect(db_path)`.

- [ ] **Step 5: Update `save_markdown_report` to use injected `reports_dir`.**
    - Update directory creation and file path joining to use `reports_dir` instead of the old `REPORTS_DIR`.
    - Implement file extension to subfolder mapping logic: `.md` -> `markdown/`.
    - Ensure `os.makedirs(reports_dir / "markdown", exist_ok=True)` is called.
    - Handle unknown extensions by returning an error.

- [ ] **Step 6: Update `export_query_to_csv` to use injected `db_path` and `reports_dir`.**
    - Replace `sqlite3.connect(DB_PATH)` with `sqlite3.connect(db_path)`.
    - Update directory creation and file path joining to use `reports_dir` instead of the old `EXPORTS_DIR`.
    - Implement file extension to subfolder mapping logic: `.csv` -> `csv/`.
    - Ensure `os.makedirs(reports_dir / "csv", exist_ok=True)` is called.
    - Handle unknown extensions by returning an error.

- [ ] **Step 7: Keep `get_current_datetime` stateless.**
    - No changes needed for `get_current_datetime`.

### Task 1.2: Refactor `backend/chat/agent.py` to use injected paths

**Files:**
- Modify: `/home/yizuz/Documents/Projects/universal-db-agent/backend/chat/agent.py`

**Interfaces:**
- Consumes: `build_tools(db_path, reports_dir)` from `backend/chat/tools.py`.
- Produces: `UniversalDBAgent` initialized with resolved `db_path` and `reports_dir`.

- [ ] **Step 1: Import `build_tools` and `pathlib.Path`.**
    - Add `from .tools import build_tools`.
    - Add `from pathlib import Path`.

- [ ] **Step 2: Modify `UniversalDBAgent.__init__` to accept `db_path` and `reports_dir`.**
    - Update `__init__` signature to `def __init__(self, provider: str = "ollama", model_name: str = "gemma4:latest", db_path: str | None = None, reports_dir: str | None = None):`.

- [ ] **Step 3: Resolve `db_path` and `reports_dir` defaults.**
    - Calculate `project_root` relative to `agent.py` (e.g., `Path(__file__).resolve().parent.parent.parent`).
    - If `db_path` is `None`, set it to `project_root / "construction_company.db"`.
    - If `reports_dir` is `None`, set it to `project_root / "reports"`.
    - Resolve any relative `db_path` or `reports_dir` to absolute paths using `project_root`.

- [ ] **Step 4: Call `build_tools` to initialize `self.tools`.**
    - Replace the hardcoded `self.tools` list with `self.tools = build_tools(db_path, reports_dir)`.

### Task 1.3: Refactor `backend/chat/services.py` to pass paths to agent

**Files:**
- Modify: `/home/yizuz/Documents/Projects/universal-db-agent/backend/chat/services.py`

**Interfaces:**
- Consumes: `UniversalDBAgent` with `db_path` and `reports_dir` parameters.

- [ ] **Step 1: Import `pathlib.Path`.**
    - Add `from pathlib import Path`.

- [ ] **Step 2: Calculate `project_root`.**
    - Define `project_root` as `Path(__file__).resolve().parent.parent.parent`.

- [ ] **Step 3: Resolve `sys_config.target_db_path` to an absolute path.**
    - If `sys_config.target_db_path` is relative, resolve it against `project_root`.
    - Ensure `reports_dir` is also set to `project_root / "reports"`.

- [ ] **Step 4: Pass `db_path` and `reports_dir` to `UniversalDBAgent`.**
    - Update `UniversalDBAgent` instantiation to include `db_path=resolved_db_path` and `reports_dir=resolved_reports_dir`.

### Task 1.4: Delete phantom DB file

**Files:**
- Delete: `/home/yizuz/Documents/Projects/universal-db-agent/backend/construction_company.db`

- [ ] **Step 1: Delete `backend/construction_company.db`.**
    - Use `rm /home/yizuz/Documents/Projects/universal-db-agent/backend/construction_company.db`.

---

### Task 2.1: Migrate existing report and export files

**Files:**
- Move: `/home/yizuz/Documents/Projects/universal-db-agent/reports/construction_status.md`
- Move: `/home/yizuz/Documents/Projects/universal-db-agent/reports/old_projects.md`
- Move: `/home/yizuz/Documents/Projects/universal-db-agent/reports/reporte_proyectos_construccion.md`
- Move: `/home/yizuz/Documents/Projects/universal-db-agent/exports/assignment_matrix.csv`
- Delete: `/home/yizuz/Documents/Projects/universal-db-agent/exports` (and any empty subfolders in `reports/`)

- [ ] **Step 1: Create new target directories if they don't exist.**
    - Ensure `project_root/reports/markdown` and `project_root/reports/csv` exist.

- [ ] **Step 2: Move Markdown files.**
    - `mv project_root/reports/construction_status.md project_root/reports/markdown/`
    - `mv project_root/reports/old_projects.md project_root/reports/markdown/`
    - `mv project_root/reports/reporte_proyectos_construccion.md project_root/reports/markdown/`

- [ ] **Step 3: Move CSV file.**
    - `mv project_root/exports/assignment_matrix.csv project_root/reports/csv/`

- [ ] **Step 4: Remove old `exports/` directory.**
    - `rmdir project_root/exports` (ensure it's empty).
    - Remove any other empty subdirectories in `reports/` if they were created before.

### Task 2.2: Refactor `backend/chat/api_views.py` for new report paths and CSV endpoint

**Files:**
- Modify: `/home/yizuz/Documents/Projects/universal-db-agent/backend/chat/api_views.py`

**Interfaces:**
- Produces: `ViewMarkdownReportView` points to `reports/markdown/`, new `ViewCSVExportView` for `reports/csv/`.

- [ ] **Step 1: Update `REPORTS_DIR` constant.**
    - Change `REPORTS_DIR = os.path.abspath("storage/reports")` to point to `project_root/reports/markdown`. Calculate `project_root` relative to `api_views.py`.

- [ ] **Step 2: Fix HTTP status code.**
    - Change `status.HTTP_444_NOT_FOUND` to `status.HTTP_404_NOT_FOUND` in `ProcessAgentMessageView`.

- [ ] **Step 3: Create `ViewCSVExportView` class.**
    - Implement a new `APIView` for `GET /api/exports/<filename>/` that serves CSV files.
    - Use `os.path.basename` for filename sanitization.
    - Ensure the file is strictly within `project_root/reports/csv`.
    - Set `content_type='text/csv'`.
    - Raise `Http404` if file not found or extension is not `.csv`.

### Task 2.3: Wire new CSV endpoint in `backend/core/urls.py`

**Files:**
- Modify: `/home/yizuz/Documents/Projects/universal-db-agent/backend/core/urls.py`

**Interfaces:**
- Consumes: `ViewCSVExportView` from `backend/chat/api_views.py`.

- [ ] **Step 1: Import `ViewCSVExportView`.**
    - Add `from chat.api_views import ViewCSVExportView`.

- [ ] **Step 2: Add URL pattern for CSV exports.**
    - Add `path("api/exports/<str:filename>/", ViewCSVExportView.as_view(), name="csv_export")`.

---

### Task 3.1: Fix CLI `main.py`

**Files:**
- Modify: `/home/yizuz/Documents/Projects/universal-db-agent/main.py`

**Interfaces:**
- Consumes: `UniversalDBAgent` from `backend/chat/agent.py`.

- [ ] **Step 1: Add path manipulation for imports.**
    - Add `import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend"))`.

- [ ] **Step 2: Correct `chat.tools` imports.**
    - Change `from src.tools import (...)` to `from chat.tools import (...)`.

- [ ] **Step 3: Correct `chat.agent` import.**
    - Change `from src.agent import UniversalDBAgent` to `from chat.agent import UniversalDBAgent`.

- [ ] **Step 4: Remove unused imports.**
    - Remove `from langchain_ollama import ChatOllama`.
    - Remove `from langchain_core.messages import HumanMessage, ToolMessage`.

- [ ] **Step 5: Ensure `UniversalDBAgent()` uses correct defaults.**
    - No direct changes needed here, as `UniversalDBAgent`'s `__init__` (modified in Task 1.2) will handle the default path resolution based on `project_root`.

---

### Task 4: Verification

**Files:** N/A (Verification output)

- [ ] **Step 1: Verify `chat.tools` functionality from `backend/`.**
    - Create a temporary script in `backend/`.
    - Import `chat.tools`, build tools with absolute paths for `db_path` and `reports_dir`.
    - Invoke `list_tables_and_columns` (must list 3 tables).
    - Invoke `execute_read_only_query('SELECT * FROM projects')` (must return 3 rows).
    - Invoke `save_markdown_report` (writes to `reports/markdown/`).
    - Invoke `get_current_datetime`.
    - Invoke `export_query_to_csv` (writes to `reports/csv/`).
    - Delete the created test files.

- [ ] **Step 2: Verify `UniversalDBAgent` initialization from project root.**
    - Run: `env -u PYTHONPATH ./venv/bin/python -c "import sys; sys.path.insert(0,'backend'); from chat.agent import UniversalDBAgent; a=UniversalDBAgent(); print([t.name for t in a.tools])"`
    - Expected: Prints the 5 tool names.

- [ ] **Step 3: Verify `main.py` execution.**
    - Run: `echo "quit" | env -u PYTHONPATH ./venv/bin/python main.py`
    - Expected: No crashes on imports, exits gracefully.

- [ ] **Step 4: Verify Django project check.**
    - Run: `cd backend && env -u PYTHONPATH ../venv/bin/python manage.py check`
    - Expected: Passes without errors.

- [ ] **Step 5: Confirm file migrations.**
    - Check for existence of files in new locations (e.g., `project_root/reports/markdown/*.md`).
    - Confirm `project_root/exports` directory is gone.
    - Confirm `backend/construction_company.db` is gone.
