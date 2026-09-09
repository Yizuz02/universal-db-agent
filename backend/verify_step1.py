
import sys
import os
import sqlite3
from pathlib import Path

# Adjust sys.path to ensure 'chat' package is found
sys.path.insert(0, str(Path(__file__).resolve().parent))

from chat.tools import build_tools

project_root = Path(__file__).resolve().parent.parent # This should be the project root
db_path = project_root / "construction_company.db"
reports_dir = project_root / "reports"
metadata_path = project_root / "backend" / "chat" / "metadata.json"

tools = build_tools(db_path, reports_dir, metadata_path)
list_tables_and_columns_tool = tools[0]
execute_read_only_query_tool = tools[1]
save_markdown_report_tool = tools[2]
get_current_datetime_tool = tools[3]
export_query_to_csv_tool = tools[4]

# 1. list_tables_and_columns (must list 3 tables)
schema = list_tables_and_columns_tool.func()
print("Schema (should list 3 tables):\n" + schema)
assert "Table 'projects'" in schema and "Table 'workers'" in schema and "Table 'assignments'" in schema, "list_tables_and_columns failed"

# 2. execute_read_only_query('SELECT * FROM projects') (must return 3 rows)
projects_data = execute_read_only_query_tool.func(query='SELECT * FROM projects') # Fixed
print("Projects data (should return 3 rows):\n" + projects_data)
assert len(projects_data.splitlines()) >= 4, "execute_read_only_query failed to return 3 rows" # Header + 3 rows

# 3. save_markdown_report (writes to reports/markdown/)
report_filename = "test_report.md"
report_content = "# Test Report\nThis is a test markdown report."
save_markdown_report_tool.func(filename=report_filename, content=report_content) # Fixed
test_report_path = reports_dir / "markdown" / report_filename
print("Test report path: " + str(test_report_path))
assert test_report_path.exists(), "save_markdown_report failed to create file"

# 4. get_current_datetime
current_datetime = get_current_datetime_tool.func()
print("Current datetime: " + current_datetime)
assert "Current Date and Time:" in current_datetime, "get_current_datetime failed"

# 5. export_query_to_csv (writes to reports/csv/)
csv_filename = "test_export.csv"
csv_query = "SELECT id, name FROM projects"
export_query_to_csv_tool.func(query=csv_query, filename=csv_filename) # Fixed
test_csv_path = reports_dir / "csv" / csv_filename
print("Test CSV path: " + str(test_csv_path))
assert test_csv_path.exists(), "export_query_to_csv failed to create file"

# Delete those two test files
os.remove(test_report_path)
os.remove(test_csv_path)
assert not test_report_path.exists(), "Failed to delete test report"
assert not test_csv_path.exists(), "Failed to delete test CSV"

print("Verification Step 1 Passed!")
