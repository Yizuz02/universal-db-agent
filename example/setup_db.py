import sqlite3


def create_database():
    conn = sqlite3.connect("construction_company.db")
    cursor = conn.cursor()

    # 1. Projects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        location TEXT,
        total_budget REAL,
        start_date TEXT,
        status TEXT -- 'Planning', 'In Progress', 'Completed'
    )
    """)

    # 2. Workers / Contractors table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS workers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        role TEXT, -- 'Engineer', 'Architect', 'Construction Worker', 'Electrician'
        hourly_rate REAL
    )
    """)

    # 3. Resource assignments table (links projects and workers)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER,
        worker_id INTEGER,
        estimated_hours INTEGER,
        FOREIGN KEY (project_id) REFERENCES projects(id),
        FOREIGN KEY (worker_id) REFERENCES workers(id)
    )
    """)

    # Insert sample data if the database is empty
    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("""
            INSERT INTO projects
            (name, location, total_budget, start_date, status)
            VALUES (?, ?, ?, ?, ?)
        """, [
            ("Altitude Tower", "Mexico City", 15000000.0, "2026-01-15", "In Progress"),
            ("Downtown Shopping Plaza", "Guadalajara", 8000000.0, "2026-03-01", "Planning"),
            ("Bicentennial Bridge", "Monterrey", 45000000.0, "2025-05-10", "Completed"),
        ])

        cursor.executemany("""
            INSERT INTO workers
            (name, role, hourly_rate)
            VALUES (?, ?, ?)
        """, [
            ("Carlos Gomez", "Engineer", 450.0),
            ("Ana Martinez", "Architect", 500.0),
            ("Jose Lopez", "Construction Worker", 120.0),
            ("Luis Rodriguez", "Electrician", 180.0),
        ])

        cursor.executemany("""
            INSERT INTO assignments
            (project_id, worker_id, estimated_hours)
            VALUES (?, ?, ?)
        """, [
            (1, 1, 120),  # Carlos assigned to Altitude Tower
            (1, 2, 80),   # Ana assigned to Altitude Tower
            (1, 3, 300),  # Jose assigned to Altitude Tower
            (2, 2, 60),   # Ana assigned to Downtown Shopping Plaza
            (3, 1, 200),  # Carlos assigned to Bicentennial Bridge
        ])

        conn.commit()
        print("🏗️ Database 'construction_company.db' created with sample data.")
    else:
        print("🔄 Database already exists and contains data.")

    conn.close()


if __name__ == "__main__":
    create_database()