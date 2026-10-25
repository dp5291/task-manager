"""Create tasks.db for the Week 7 MCP project (seeded from the TASKS/USERS data)."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("tasks.db")

TASKS = [
    (1, "Buy groceries", "completed", "Alice", "2026-10-20"),
    (2, "Write report", "open", "Alice", "2026-10-30"),
    (3, "Call dentist", "completed", "Bob", "2026-10-18"),
    (4, "Write unit tests", "open", "Alice", "2026-11-02"),
    (5, "Fix login bug", "in_progress", "Bob", "2026-10-28"),
    (6, "Review pull request", "open", "Bob", "2026-11-05"),
    (7, "Update README", "in_progress", "Alice", "2026-11-01"),
]

conn = sqlite3.connect(DB_PATH)
conn.execute(
    """CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        status TEXT NOT NULL CHECK (status IN ('open', 'in_progress', 'completed')),
        assigned_to TEXT NOT NULL,
        due_date TEXT
    )"""
)
conn.execute("DELETE FROM tasks")  # make the script safe to re-run
conn.executemany("INSERT INTO tasks VALUES (?, ?, ?, ?, ?)", TASKS)
conn.commit()
for row in conn.execute("SELECT * FROM tasks ORDER BY id"):
    print(row)
conn.close()