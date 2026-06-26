"""IRIS v8 Database — SQLite with full schema for all IRIS data"""
import os
import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from config import config

class Database:
    """Central SQLite database for IRIS v8."""

    def __init__(self):
        self.db_path = config.DATABASE_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else ".", exist_ok=True)
        self._init_tables()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_tables(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        # Messages (chat history)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                reasoning TEXT,
                tool_calls TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tasks
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                estimated_duration INTEGER,
                steps TEXT,
                result TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        """)

        # Memories (semantic)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                importance INTEGER DEFAULT 5,
                source TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Episodes (events)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                context TEXT,
                emotion TEXT DEFAULT 'neutral',
                lesson TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Owner profile
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS owner (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT DEFAULT 'Infinite Vybeflix',
                aliases TEXT DEFAULT 'Infinite',
                preferences TEXT,
                personality_notes TEXT,
                tech_stack_prefs TEXT,
                project_history TEXT,
                secrets TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Calendar events
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_time TEXT NOT NULL,
                end_time TEXT,
                location TEXT,
                category TEXT DEFAULT 'general',
                priority INTEGER DEFAULT 5,
                notified INTEGER DEFAULT 0,
                recurring TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Notes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                category TEXT DEFAULT 'general',
                tags TEXT,
                pinned INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                component TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT DEFAULT 'owner',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                last_active TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Insert default owner if not exists
        cursor.execute("INSERT OR IGNORE INTO owner (id, name, aliases) VALUES (1, ?, ?)",
                      (config.OWNER_NAME, config.OWNER_ALIAS))

        conn.commit()
        conn.close()

    # === MESSAGES ===
    def save_message(self, session_id: str, role: str, content: str, reasoning: str = None, tool_calls: List[str] = None):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO messages (session_id, role, content, reasoning, tool_calls) VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, reasoning, json.dumps(tool_calls) if tool_calls else None)
        )
        conn.commit()
        conn.close()

    def get_conversation(self, session_id: str, limit: int = 50) -> List[Dict]:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY timestamp DESC LIMIT ?",
            (session_id, limit)
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows[::-1]  # Oldest first

    # === TASKS ===
    def create_task(self, task_id: str, description: str, priority: int = 5, estimated_duration: int = None):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO tasks (id, description, priority, estimated_duration) VALUES (?, ?, ?, ?)",
            (task_id, description, priority, estimated_duration)
        )
        conn.commit()
        conn.close()

    def update_task(self, task_id: str, status: str = None, steps: List = None, result: str = None):
        conn = self._get_conn()
        updates = []
        params = []
        if status:
            updates.append("status = ?")
            params.append(status)
        if steps is not None:
            updates.append("steps = ?")
            params.append(json.dumps(steps))
        if result:
            updates.append("result = ?")
            params.append(result)
        if status == "completed":
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())
        if updates:
            params.append(task_id)
            conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?", params)
            conn.commit()
        conn.close()

    # === MEMORIES ===
    def save_memory(self, key: str, value: str, category: str = "general", importance: int = 5, source: str = None):
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO memories (key, value, category, importance, source)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(key) DO UPDATE SET
               value = excluded.value,
               category = excluded.category,
               importance = excluded.importance,
               timestamp = CURRENT_TIMESTAMP""",
            (key, value, category, importance, source)
        )
        conn.commit()
        conn.close()

    def search_memory(self, query: str, category: str = None, limit: int = 10) -> List[Dict]:
        conn = self._get_conn()
        if category:
            cursor = conn.execute(
                "SELECT * FROM memories WHERE category = ? AND (key LIKE ? OR value LIKE ?) ORDER BY importance DESC, timestamp DESC LIMIT ?",
                (category, f"%{query}%", f"%{query}%", limit)
            )
        else:
            cursor = conn.execute(
                "SELECT * FROM memories WHERE key LIKE ? OR value LIKE ? ORDER BY importance DESC, timestamp DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", limit)
            )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    # === EPISODES ===
    def save_episode(self, event: str, context: str = None, emotion: str = "neutral", lesson: str = None):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO episodes (event, context, emotion, lesson) VALUES (?, ?, ?, ?)",
            (event, context, emotion, lesson)
        )
        conn.commit()
        conn.close()

    def get_episodes(self, limit: int = 20) -> List[Dict]:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM episodes ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    # === OWNER ===
    def get_owner(self) -> Dict:
        conn = self._get_conn()
        cursor = conn.execute("SELECT * FROM owner WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {}

    def update_owner(self, **kwargs):
        conn = self._get_conn()
        for key, value in kwargs.items():
            conn.execute(f"UPDATE owner SET {key} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = 1", (value,))
        conn.commit()
        conn.close()

    # === CALENDAR ===
    def add_calendar_event(self, title: str, start_time: str, end_time: str = None,
                           description: str = None, location: str = None,
                           category: str = "general", priority: int = 5, recurring: str = None) -> int:
        conn = self._get_conn()
        cursor = conn.execute(
            """INSERT INTO calendar_events
               (title, description, start_time, end_time, location, category, priority, recurring)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, description, start_time, end_time, location, category, priority, recurring)
        )
        event_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return event_id

    def get_calendar_events(self, start: str = None, end: str = None, category: str = None) -> List[Dict]:
        conn = self._get_conn()
        query = "SELECT * FROM calendar_events WHERE 1=1"
        params = []
        if start:
            query += " AND start_time >= ?"
            params.append(start)
        if end:
            query += " AND start_time <= ?"
            params.append(end)
        if category:
            query += " AND category = ?"
            params.append(category)
        query += " ORDER BY start_time"
        cursor = conn.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_upcoming_events(self, hours: int = 24) -> List[Dict]:
        from datetime import datetime, timedelta
        now = datetime.now().isoformat()
        future = (datetime.now() + timedelta(hours=hours)).isoformat()
        return self.get_calendar_events(start=now, end=future)

    def mark_notified(self, event_id: int):
        conn = self._get_conn()
        conn.execute("UPDATE calendar_events SET notified = 1 WHERE id = ?", (event_id,))
        conn.commit()
        conn.close()

    # === NOTES ===
    def add_note(self, title: str, content: str = "", category: str = "general", tags: List[str] = None) -> int:
        conn = self._get_conn()
        cursor = conn.execute(
            "INSERT INTO notes (title, content, category, tags) VALUES (?, ?, ?, ?)",
            (title, content, category, json.dumps(tags or []))
        )
        note_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return note_id

    def get_notes(self, category: str = None, search: str = None) -> List[Dict]:
        conn = self._get_conn()
        query = "SELECT * FROM notes WHERE 1=1"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if search:
            query += " AND (title LIKE ? OR content LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        query += " ORDER BY pinned DESC, updated_at DESC"
        cursor = conn.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def update_note(self, note_id: int, **kwargs):
        conn = self._get_conn()
        for key, value in kwargs.items():
            conn.execute(f"UPDATE notes SET {key} = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (value, note_id))
        conn.commit()
        conn.close()

    # === LOGS ===
    def log(self, level: str, component: str, message: str):
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO logs (level, component, message) VALUES (?, ?, ?)",
            (level, component, message)
        )
        conn.commit()
        conn.close()

    # === SESSIONS ===
    def create_session(self, session_id: str, user_id: str = "owner", expires_hours: int = 24):
        from datetime import timedelta
        expires = (datetime.now() + timedelta(hours=expires_hours)).isoformat()
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO sessions (session_id, user_id, expires_at) VALUES (?, ?, ?)",
            (session_id, user_id, expires)
        )
        conn.commit()
        conn.close()

    def validate_session(self, session_id: str) -> bool:
        conn = self._get_conn()
        cursor = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ? AND expires_at > ?",
            (session_id, datetime.now().isoformat())
        )
        valid = cursor.fetchone() is not None
        if valid:
            conn.execute("UPDATE sessions SET last_active = CURRENT_TIMESTAMP WHERE session_id = ?", (session_id,))
            conn.commit()
        conn.close()
        return valid

# Singleton
db = Database()
