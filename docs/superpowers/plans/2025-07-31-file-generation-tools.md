# Per-Type File-Generation Tools (Markdown / CSV / Excel) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add per-type file-generation tools (Markdown, CSV, Excel) that persist a DB record linked to the conversation, plus a file bubble in the chat UI with preview + download.

**Architecture:** Extend the existing tools/agent/services/api/frontend stack. Each save tool creates a file in a typed subfolder under reports/, records a `GeneratedFile` DB row, and the API exposes preview/download endpoints. The frontend renders file bubbles on agent messages and a preview modal.

**Tech Stack:** Django 6.0.7, React 19 + Vite + Tailwind, langchain, openpyxl, sqlite3

## Global Constraints

- `env -u PYTHONPATH ./venv/bin/python ...` for all Python commands from project root
- Do not touch running Django (port 8765) or Vite (port 5173) dev servers
- openpyxl installed via `env -u PYTHONPATH ./venv/bin/pip install openpyxl`
- Keep existing delete/rename/auto-title behaviors intact
- Do not touch: settings panel, FilesModal, backend reports/exports serving endpoints

---

### Task 1: Install openpyxl

**Files:**
- (none modified)

- [ ] **Step 1: Install openpyxl**

```bash
cd /home/yizuz/Documents/Projects/universal-db-agent && env -u PYTHONPATH ./venv/bin/pip install openpyxl
```

- [ ] **Step 2: Verify import**

```bash
env -u PYTHONPATH ./venv/bin/python -c "import openpyxl; print(openpyxl.__version__)"
```

---

### Task 2: Rename/add tools in backend/chat/tools.py

**Files:**
- Modify: `backend/chat/tools.py`

**Interfaces:**
- Produces: `build_tools(db_path, reports_dir, metadata_path, on_file_saved=None)` — updated signature
- Produces: `save_markdown_report(filename, content)` (renamed, stays)
- Produces: `save_csv_report(query, filename)` (renamed from `export_query_to_csv`)
- Produces: `save_excel_report(query, filename)` (new)
- Produces: `SaveReportInput`, `SaveCSVReportInput`, `SaveExcelReportInput` pydantic schemas

- [ ] **Step 1: Rename `ExportCSVInput` to `SaveCSVReportInput`**

In `backend/chat/tools.py`, rename the class and update its tool reference.

- [ ] **Step 2: Add `SaveExcelReportInput` pydantic schema**

```python
class SaveExcelReportInput(BaseModel):
    query: str = Field(
        description="The exact SQL SELECT query to execute to fetch the data for the Excel file. Must be read-only."
    )
    filename: str = Field(
        description="The name of the Excel file to generate (e.g., 'project_report.xlsx'). Must include the .xlsx extension."
    )
```

- [ ] **Step 3: Rename `export_query_to_csv` tool to `save_csv_report`**

Change the function name, update the `args_schema` decorator reference to `SaveCSVReportInput`.

- [ ] **Step 4: Add `on_file_saved` parameter to `build_tools`**

```python
def build_tools(db_path: Path, reports_dir: Path, metadata_path: Path, on_file_saved=None):
```

- [ ] **Step 5: Add `on_file_saved(file_path)` call to `save_markdown_report`**

After `with open(file_path, "w", ...) as f: f.write(content)` but before the return, add:
```python
if on_file_saved:
    on_file_saved(str(file_path))
```

- [ ] **Step 6: Add `on_file_saved(file_path)` call to `save_csv_report`**

Same pattern, after `writer.writerows(rows)` but before the return.

- [ ] **Step 7: Add `.xlsx` → `excel` mapping to extension validation in `save_markdown_report` and `save_csv_report`**

In the extension check logic, ensure `.xlsx` is recognized. For `save_markdown_report`, only `.md` is valid. For `save_csv_report`, only `.csv` is valid. No changes needed to existing validations.

- [ ] **Step 8: Create `save_excel_report` tool**

```python
@tool(args_schema=SaveExcelReportInput)
def save_excel_report(query: str, filename: str) -> str:
    """
    Executes a SQL SELECT query, extracts the records, and exports them into a real Excel (.xlsx) spreadsheet file.
    Use this tool ONLY when the user explicitly asks to save to an Excel file.
    """
    import openpyxl
    from openpyxl.styles import Font
    
    query_clean = query.strip().lower()
    if not query_clean.startswith("select"):
        return "Error: For security reasons, only read-only queries (SELECT) are permitted for Excel exports."
        
    file_extension = Path(filename).suffix
    if file_extension.lower() != ".xlsx":
        return f"Error: Only Excel files (.xlsx) are supported for Excel exports. Received: {file_extension}"

    target_dir = reports_dir / "excel"

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        safe_filename = Path(filename).name
        file_path = target_dir / safe_filename
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        headers = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "The query executed successfully but returned no data to export."
            
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Report"
        
        bold_font = Font(bold=True)
        for col_idx, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = bold_font
        
        for row_idx, row in enumerate(rows, 2):
            for col_idx, value in enumerate(row, 1):
                ws.cell(row=row_idx, column=col_idx, value=value)
                
        wb.save(str(file_path))
        
        if on_file_saved:
            on_file_saved(str(file_path))
            
        return f"Success: Data successfully exported to an Excel file at '{file_path}' ({len(rows)} records exported)."
        
    except sqlite3.Error as e:
        return f"SQL Execution Error during Excel export: {str(e)}. Please check syntax and try again."
    except Exception as e:
        return f"Error creating Excel file: {str(e)}"
```

- [ ] **Step 9: Update the return list at the bottom of `build_tools`**

Include `save_excel_report` in the return list.

---

### Task 3: Pass on_file_saved through agent

**Files:**
- Modify: `backend/chat/agent.py:43`

**Interfaces:**
- Consumes: `build_tools(db_path, reports_dir, metadata_path, on_file_saved=None)` from Task 2
- Produces: `UniversalDBAgent.__init__` accepts optional `on_file_saved` parameter

- [ ] **Step 1: Add `on_file_saved` param to `UniversalDBAgent.__init__`**

```python
def __init__(self, provider: str = "ollama", model_name: str = "gemma4:latest", db_path: str | None = None, reports_dir: str | None = None, metadata_path: str | None = None, on_file_saved=None):
```

- [ ] **Step 2: Pass `on_file_saved` through to `build_tools`**

```python
self.tools = build_tools(resolved_db_path, resolved_reports_dir, resolved_metadata_path, on_file_saved=on_file_saved)
```

---

### Task 4: Add GeneratedFile model + migration

**Files:**
- Modify: `backend/chat/models.py`
- Create: migration file (auto-generated by makemigrations)

**Interfaces:**
- Produces: `GeneratedFile` model with fields: message (FK → Message), conversation (FK → Conversation), filename, extension, file_path, size_bytes, created_at

- [ ] **Step 1: Add `GeneratedFile` model to `backend/chat/models.py`**

```python
class GeneratedFile(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='generated_files')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='generated_files')
    filename = models.CharField(max_length=255)
    extension = models.CharField(max_length=10)
    file_path = models.CharField(max_length=500)
    size_bytes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.extension})"
```

- [ ] **Step 2: Run makemigrations**

```bash
cd /home/yizuz/Documents/Projects/universal-db-agent/backend && env -u PYTHONPATH ../venv/bin/python manage.py makemigrations chat
```

- [ ] **Step 3: Run migrate**

```bash
cd /home/yizuz/Documents/Projects/universal-db-agent/backend && env -u PYTHONPATH ../venv/bin/python manage.py migrate
```

- [ ] **Step 4: Verify table exists**

```bash
sqlite3 /home/yizuz/Documents/Projects/universal-db-agent/backend/db.sqlite3 "PRAGMA table_info(chat_generatedfile);"
```

---

### Task 5: Wire file generation to DB in services.py

**Files:**
- Modify: `backend/chat/services.py`

**Interfaces:**
- Consumes: `GeneratedFile` model from Task 4, `on_file_saved` from Task 3
- Produces: `execute_agent_and_save_workflow` creates `GeneratedFile` rows and returns unchanged `(agent_response, new_title)` signature

- [ ] **Step 1: Import `GeneratedFile` and `os`**

```python
from .models import Conversation, Message, MessageToolCall, GeneratedFile
import os
```

- [ ] **Step 2: Add `on_file_saved` callback in `execute_agent_and_save_workflow`**

Before creating the agent, define a list:
```python
collected_paths = []
```

Pass `on_file_saved=collected_paths.append` to the agent's constructor.

- [ ] **Step 3: Create `GeneratedFile` records after the final agent message**

Inside the transaction block, after `Message.objects.create(..., role='agent', content=agent_response, has_tool_calls=False)` (but before the auto-title logic), add:

```python
final_agent_message = Message.objects.get(
    conversation=conversation,
    role='agent',
    has_tool_calls=False,
    created_at__gte=...  # need to capture the message object directly
)
```

Better approach: capture the message object:
```python
final_agent_message = Message.objects.create(
    conversation=conversation,
    role='agent',
    content=agent_response,
    has_tool_calls=False
)
```

Then iterate:
```python
for path in collected_paths:
    try:
        filename = os.path.basename(path)
        extension = os.path.splitext(path)[1].lstrip('.')
        size = os.path.getsize(path)
        GeneratedFile.objects.create(
            message=final_agent_message,
            conversation=conversation,
            filename=filename,
            extension=extension,
            file_path=path,
            size_bytes=size,
        )
    except Exception:
        logger.warning("Failed to create GeneratedFile record for %s", path, exc_info=True)
```

- [ ] **Step 4: Verify return value unchanged**

The function still returns `return agent_response, None` or `return agent_response, new_title`. No signature change.

---

### Task 6: Add serializers for GeneratedFile

**Files:**
- Modify: `backend/chat/serializers.py`

**Interfaces:**
- Produces: `GeneratedFileSerializer` with fields id, filename, extension, size_bytes, created_at
- Modifies: `MessageSerializer` to include `files = GeneratedFileSerializer(many=True, read_only=True)`

- [ ] **Step 1: Import `GeneratedFile`**

```python
from .models import Conversation, Message, MessageToolCall, GeneratedFile
```

- [ ] **Step 2: Add `GeneratedFileSerializer`**

```python
class GeneratedFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedFile
        fields = ['id', 'filename', 'extension', 'size_bytes', 'created_at']
        read_only_fields = ['id', 'created_at']
```

- [ ] **Step 3: Add `files` field to `MessageSerializer`**

```python
class MessageSerializer(serializers.ModelSerializer):
    tool_calls = MessageToolCallSerializer(many=True, read_only=True)
    files = GeneratedFileSerializer(many=True, read_only=True)
    # ... Meta unchanged
```

Update `Meta.fields` to include `'files'`.

---

### Task 7: Add API endpoints for file preview and download

**Files:**
- Modify: `backend/chat/api_views.py`
- Modify: `backend/chat/urls.py`
- Modify: `backend/core/urls.py` (only if needed — actually chat/urls.py handles it)

**Interfaces:**
- Produces: `GET /api/files/<int:file_id>/download/` → FileResponse
- Produces: `GET /api/files/<int:file_id>/preview/` → JSON
- Modifies: `ProcessAgentMessageView.post` response to include `files` key

- [ ] **Step 1: Add imports to `api_views.py`**

```python
import csv
import openpyxl
from io import StringIO
from .models import Conversation, GeneratedFile
from .serializers import (..., GeneratedFileSerializer)
```

- [ ] **Step 2: Create `FileDownloadView`**

```python
class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        try:
            gf = GeneratedFile.objects.select_related('conversation').get(id=file_id)
        except GeneratedFile.DoesNotExist:
            raise Http404("File not found.")
        if gf.conversation.user != request.user:
            raise Http404("File not found.")
        if not os.path.exists(gf.file_path):
            raise Http404("File missing from disk.")
        return FileResponse(open(gf.file_path, 'rb'), as_attachment=True, filename=gf.filename)
```

- [ ] **Step 3: Create `FilePreviewView`**

```python
class FilePreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        try:
            gf = GeneratedFile.objects.select_related('conversation').get(id=file_id)
        except GeneratedFile.DoesNotExist:
            return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)
        if gf.conversation.user != request.user:
            return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            with open(gf.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return Response({"error": "File missing from disk."}, status=status.HTTP_404_NOT_FOUND)

        ext = gf.extension.lower()
        if ext == 'md':
            return Response({"type": "markdown", "content": content})
        elif ext == 'csv':
            reader = csv.reader(StringIO(content))
            rows = [row for row in reader]
            headers = rows[0] if rows else []
            data_rows = rows[1:] if len(rows) > 1 else []
            return Response({"type": "csv", "headers": headers, "rows": data_rows})
        elif ext == 'xlsx':
            import openpyxl
            from io import BytesIO
            with open(gf.file_path, 'rb') as f:
                wb = openpyxl.load_workbook(BytesIO(f.read()), read_only=True)
            ws = wb.active
            all_rows = [[str(cell.value) if cell.value is not None else '' for cell in row] for row in ws.iter_rows()]
            wb.close()
            headers = all_rows[0] if all_rows else []
            data_rows = all_rows[1:] if len(all_rows) > 1 else []
            return Response({"type": "excel", "headers": headers, "rows": data_rows})
        else:
            return Response({"error": "Unsupported file type."}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
```

- [ ] **Step 4: Add URL patterns to `chat/urls.py`**

```python
from .api_views import (
    ...
    FileDownloadView,
    FilePreviewView,
)

# Add to urlpatterns:
path("api/files/<int:file_id>/download/", FileDownloadView.as_view(), name="file-download"),
path("api/files/<int:file_id>/preview/", FilePreviewView.as_view(), name="file-preview"),
```

- [ ] **Step 5: Modify `ProcessAgentMessageView.post` to include files**

After `final_reply, new_title = execute_agent_and_save_workflow(...)`:
```python
files_qs = GeneratedFile.objects.filter(
    conversation=conversation,
).order_by('-created_at')[:20]  # get recent files for this turn
response_data = {"agent_response": final_reply, "files": GeneratedFileSerializer(files_qs, many=True).data}
```

Actually, we need to be more precise about which files belong to *this turn*. The `collected_paths` are inside the service function. Options:
1. Return collected_paths from the service function and query by path
2. Get the most recent agent message and filter by that

Best approach: modify `execute_agent_and_save_workflow` to also return the list of `GeneratedFile` IDs or the serialized data. Let's return a third value.

Update `services.py` return to include `(agent_response, new_title, generated_file_ids)`, then query by those IDs in the view.

**Alternative simpler approach**: In the service, create the GeneratedFile records, then return their IDs. In the view, query by those IDs.

Modify `services.py`:
```python
generated_file_ids = []
...
for path in collected_paths:
    ...
    gf = GeneratedFile.objects.create(...)
    generated_file_ids.append(gf.id)
```

Return: `return agent_response, new_title, generated_file_ids` (or just the list when no title is generated: `return agent_response, None, generated_file_ids`)

Update the view:
```python
final_reply, new_title, file_ids = execute_agent_and_save_workflow(conversation, user_text)
files_data = GeneratedFileSerializer(
    GeneratedFile.objects.filter(id__in=file_ids),
    many=True
).data
response_data = {"agent_response": final_reply, "files": files_data}
```

---

### Task 8: Add frontend API helpers

**Files:**
- Modify: `frontend/src/services/api.js`

**Interfaces:**
- Produces: `getFilePreview(fileId)` → GET /api/files/:id/preview/
- Produces: `downloadFile(fileId)` → triggers browser download via authenticated blob fetch

- [ ] **Step 1: Add `getFilePreview`**

```javascript
export const getFilePreview = (fileId) =>
  api.get(`/api/files/${fileId}/preview/`);
```

- [ ] **Step 2: Add `downloadFile`**

```javascript
export const downloadFile = async (fileId) => {
  const token = localStorage.getItem('access_token');
  const response = await fetch(`/api/files/${fileId}/download/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) throw new Error('Download failed');
  const blob = await response.blob();
  const disposition = response.headers.get('Content-Disposition');
  let filename = 'download';
  if (disposition) {
    const match = disposition.match(/filename="?(.+?)"?$/);
    if (match) filename = match[1];
  }
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
```

---

### Task 9: Add i18n keys for file UI

**Files:**
- Modify: `frontend/src/i18n/index.js`

**Interfaces:**
- Produces: i18n keys `file.preview`, `file.download`, `file.preview_error`, `file.loading` in all languages (en, es, zh, pt)

- [ ] **Step 1: Add file keys to each language**

```javascript
// en:
"file.preview": "Preview",
"file.download": "Download",
"file.preview_error": "Could not load preview.",
"file.loading": "Loading preview...",

// es:
"file.preview": "Vista previa",
"file.download": "Descargar",
"file.preview_error": "No se pudo cargar la vista previa.",
"file.loading": "Cargando vista previa...",

// zh:
"file.preview": "预览",
"file.download": "下载",
"file.preview_error": "无法加载预览。",
"file.loading": "加载预览中...",

// pt:
"file.preview": "Visualizar",
"file.download": "Baixar",
"file.preview_error": "Não foi possível carregar a visualização.",
"file.loading": "Carregando visualização...",
```

---

### Task 10: Update ChatPage.jsx with file bubbles and preview modal

**Files:**
- Modify: `frontend/src/pages/ChatPage.jsx`

**Interfaces:**
- Consumes: `getFilePreview`, `downloadFile` from api.js
- Produces: File bubble rendering below agent messages, PreviewModal component

- [ ] **Step 1: Import new API functions and create state**

```javascript
import { getFilePreview, downloadFile } from '../services/api';

// In component, add state:
const [previewData, setPreviewData] = useState(null); // { type, content/headers/rows }
const [previewLoading, setPreviewLoading] = useState(false);
const [previewError, setPreviewError] = useState('');
```

- [ ] **Step 2: Create preview open handler**

```javascript
const handlePreview = async (fileId) => {
  setPreviewLoading(true);
  setPreviewError('');
  setPreviewData(null);
  try {
    const { data } = await getFilePreview(fileId);
    setPreviewData(data);
  } catch {
    setPreviewError(t('file.preview_error'));
  } finally {
    setPreviewLoading(false);
  }
};
```

- [ ] **Step 3: Add file bubbles to agent messages**

In the message rendering, for agent messages (not tool-call messages), below the ReactMarkdown content, add:

```jsx
{m.files && m.files.length > 0 && (
  <div className="mt-3 flex flex-wrap gap-2">
    {m.files.map(f => (
      <div key={f.id} className="flex items-center gap-2 rounded-lg border px-3 py-2 text-xs"
        style={{ borderColor, backgroundColor: 'var(--color-page)' }}>
        <span className="material-symbols-outlined text-base">
          {f.extension === 'md' ? 'description' : (f.extension === 'csv' || f.extension === 'xlsx') ? 'table_chart' : 'insert_drive_file'}
        </span>
        <span className="font-medium" style={{ color: textColor }}>{f.filename}</span>
        <button onClick={() => handlePreview(f.id)} className="ml-1 rounded p-1 hover:brightness-110"
          style={{ color: mutedColor }} title={t('file.preview')}>
          <span className="material-symbols-outlined text-sm">visibility</span>
        </button>
        <button onClick={() => downloadFile(f.id)} className="rounded p-1 hover:brightness-110"
          style={{ color: mutedColor }} title={t('file.download')}>
          <span className="material-symbols-outlined text-sm">download</span>
        </button>
      </div>
    ))}
  </div>
)}
```

- [ ] **Step 4: Attach files to agent message on send**

In `handleSend`, after the API response:
```javascript
setMessages(ms => [...ms, {
  id: `tmp-${++tmpId.current}`,
  role: 'agent',
  content: data.agent_response,
  files: data.files || [],
  created_at: new Date().toISOString()
}]);
```

- [ ] **Step 5: Build PreviewModal inline**

Add a modal just before the closing `</div>` of the main container (similar to delete confirmation modal):

```jsx
{(previewData || previewLoading || previewError) && (
  <div onClick={() => { setPreviewData(null); setPreviewError(''); }}
    className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
    <div className="mx-4 w-full max-w-4xl max-h-[80vh] overflow-y-auto rounded-2xl border p-6 shadow-2xl"
      style={{ backgroundColor: surfaceBg, borderColor }}
      onClick={e => e.stopPropagation()}>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold" style={{ color: textColor }}>{t('file.preview')}</h3>
        <button onClick={() => { setPreviewData(null); setPreviewError(''); }}
          className="rounded-lg p-1 transition hover:brightness-110" style={{ color: mutedColor }}>
          <span className="material-symbols-outlined">close</span>
        </button>
      </div>
      {previewLoading && <p style={{ color: mutedColor }}>{t('file.loading')}</p>}
      {previewError && <p className="text-red-500">{previewError}</p>}
      {previewData && previewData.type === 'markdown' && (
        <div className="md p-4 rounded-xl" style={{ borderColor, backgroundColor: 'var(--color-page)' }}>
          <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>{previewData.content}</ReactMarkdown>
        </div>
      )}
      {(previewData && (previewData.type === 'csv' || previewData.type === 'excel')) && (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-sm" style={{ color: textColor }}>
            <thead>
              <tr>
                {previewData.headers.map((h, i) => (
                  <th key={i} className="border px-3 py-2 text-left font-semibold" style={{ borderColor, backgroundColor: 'var(--color-page)' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {previewData.rows.map((row, ri) => (
                <tr key={ri}>
                  {row.map((cell, ci) => (
                    <td key={ci} className="border px-3 py-1.5" style={{ borderColor }}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  </div>
)}
```

- [ ] **Step 6: Handle download in ChatPage**

Import `downloadFile` and use it in the download button — already covered in Step 3.

---

### Task 11: Verification

- [ ] **Step 1: Django check**

```bash
cd /home/yizuz/Documents/Projects/universal-db-agent/backend && env -u PYTHONPATH ../venv/bin/python manage.py check
```
Expected: "System check identified no issues"

- [ ] **Step 2: Verify migration applied**

```bash
sqlite3 /home/yizuz/Documents/Projects/universal-db-agent/backend/db.sqlite3 "PRAGMA table_info(chat_generatedfile);"
```
Expected: 7 columns (id, filename, extension, file_path, size_bytes, created_at, message_id, conversation_id)

- [ ] **Step 3: Verify openpyxl import**

```bash
env -u PYTHONPATH /home/yizuz/Documents/Projects/universal-db-agent/venv/bin/python -c "import openpyxl; print(openpyxl.__version__)"
```

- [ ] **Step 4: Functional tools test**

From project root, run a Python script that builds tools and invokes all three save tools with a real query:
```bash
cd /home/yizuz/Documents/Projects/universal-db-agent && env -u PYTHONPATH ./venv/bin/python -c "
import sys; sys.path.insert(0, 'backend')
import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django; django.setup()
from pathlib import Path
from chat.tools import build_tools

collected = []
tools_map = {t.name: t for t in build_tools(
    db_path=Path('backend/db.sqlite3'),
    reports_dir=Path('reports'),
    metadata_path=Path('backend/chat/metadata.json'),
    on_file_saved=collected.append
)}

# Test markdown
r = tools_map['save_markdown_report'].invoke({'filename': 'test_report.md', 'content': '# Test\nHello world'})
print('md:', r)

# Test csv
r = tools_map['save_csv_report'].invoke({'query': 'SELECT * FROM projects LIMIT 2', 'filename': 'test_export.csv'})
print('csv:', r)

# Test excel
r = tools_map['save_excel_report'].invoke({'query': 'SELECT * FROM projects LIMIT 2', 'filename': 'test_export.xlsx'})
print('xlsx:', r)

print('collected:', collected)
"
```

- [ ] **Step 5: Clean up test files**

```bash
rm -f /home/yizuz/Documents/Projects/universal-db-agent/reports/markdown/test_report.md
rm -f /home/yizuz/Documents/Projects/universal-db-agent/reports/csv/test_export.csv
rm -f /home/yizuz/Documents/Projects/universal-db-agent/reports/excel/test_export.xlsx
rmdir --ignore-fail-on-non-empty /home/yizuz/Documents/Projects/universal-db-agent/reports/excel
```

- [ ] **Step 6: Frontend build**

```bash
cd /home/yizuz/Documents/Projects/universal-db-agent/frontend && npm run build
```
Expected: build succeeds with no errors
