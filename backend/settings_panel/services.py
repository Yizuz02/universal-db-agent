import os
import sqlite3
import json

_data_dir = os.environ.get('DATA_DIR')
if _data_dir:
    CONFIG_DIR = os.path.join(_data_dir, "storage", "config")
else:
    CONFIG_DIR = "storage/config"
METADATA_PATH = os.path.join(CONFIG_DIR, "metadata.json")

def sync_database_schema_to_metadata(db_path: str) -> dict:
    """
    Inspects any live SQLite database, extracts its schema structure,
    and merges it into the metadata structure without deleting existing descriptions.
    """
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Target database not found at: {db_path}")

    # 1. Ensure config directory exists
    os.makedirs(CONFIG_DIR, exist_ok=True)

    # 2. Load existing metadata if file exists, otherwise start clean
    current_metadata = {}
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                current_metadata = json.load(f)
        except json.JSONDecodeError:
            current_metadata = {}

    # Initialize basic structure if empty
    if "database_description" not in current_metadata:
        current_metadata["database_description"] = "Automatically synchronized database schema. Please update this description."
    if "tables" not in current_metadata:
        current_metadata["tables"] = {}

    # 3. Connect to the live target database to inspect the real schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query all user tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    live_tables = [row[0] for row in cursor.fetchall()]

    updated_tables = {}

    for table_name in live_tables:
        # Fetch columns for this table
        cursor.execute(f"PRAGMA table_info({table_name});")
        # Structure: col[1] is column name, col[2] is data type (TEXT, INTEGER, etc.)
        live_columns = {col[1]: f"{col[2]}" for col in cursor.fetchall()}

        # Check if this table already had metadata documented by the user
        existing_table_meta = current_metadata["tables"].get(table_name, {})
        
        table_description = existing_table_meta.get("description", "No description provided yet.")
        existing_annotations = existing_table_meta.get("column_annotations", {})

        # Merge column annotations incrementally
        updated_annotations = {}
        for col_name, col_type in live_columns.items():
            # If the user already had an annotation for this column, keep it!
            # Otherwise, create an empty placeholder specifying its data type
            updated_annotations[col_name] = existing_annotations.get(
                col_name, 
                f"[{col_type}] Placeholder description for this column."
            )

        # Reconstruct the table metadata shell
        updated_tables[table_name] = {
            "description": table_description,
            "column_annotations": updated_annotations
        }

    conn.close()

    # 4. Update and persist the metadata structure
    current_metadata["tables"] = updated_tables

    with open(METADATA_PATH, "w", encoding="utf-8") as f:
        json.dump(current_metadata, f, indent=2, ensure_ascii=False)

    return current_metadata