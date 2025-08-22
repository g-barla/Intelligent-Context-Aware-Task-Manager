
import sqlite3
from datetime import datetime

DB_PATH = "tasks.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        '''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            priority INTEGER DEFAULT 3,
            deadline TEXT,
            status TEXT DEFAULT 'open',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            completed_at TEXT
            -- If you previously added completed_reason TEXT, leaving it is fine.
        )
        '''
    )
    conn.commit()
    conn.close()

def add_task(description, priority="3", deadline=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks(description, priority, deadline) VALUES(?,?,?)",
        (description, int(priority), deadline if deadline else None),
    )
    conn.commit()
    conn.close()

def list_tasks():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE status='open' ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def complete_task(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET status='done', completed_at=? WHERE task_id=?",
        (datetime.utcnow().isoformat(), task_id),
    )
    conn.commit()
    conn.close()
def list_completed():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tasks WHERE status='done' ORDER BY completed_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def reopen_task(task_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET status='open', completed_at=NULL WHERE task_id=?",
        (task_id,),
    )
    conn.commit()
    conn.close()

def set_completed_reason(task_id, reason):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE tasks SET completed_reason=? WHERE task_id=?",
        (reason, task_id),
    )
    conn.commit()
    conn.close()