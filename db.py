"""IRIS v7 Database Layer"""
import sqlite3
import os
import json
from datetime import datetime
from config import config

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or config.DATABASE_URL.replace("sqlite:///", "")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_calls TEXT,
                reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                priority INTEGER DEFAULT 5,
                steps TEXT,
                result TEXT,
                error TEXT,
                estimated_duration INTEGER,
                started_at TIMESTAMP,
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                importance INTEGER DEFAULT 5,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                context TEXT,
                emotion TEXT,
                lesson TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                content TEXT,
                summary TEXT,
                chunks TEXT,
                vector_id TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                repo_url TEXT,
                local_path TEXT,
                description TEXT,
                tech_stack TEXT,
                status TEXT DEFAULT 'active',
                last_commit TEXT,
                vercel_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                code TEXT,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                component TEXT NOT NULL,
                message TEXT NOT NULL,
                stack_trace TEXT,
                resolved INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS owner_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                name TEXT DEFAULT 'Infinite Vybeflix',
                aliases TEXT,
                preferences TEXT,
                personality_notes TEXT,
                tech_stack_prefs TEXT,
                project_history TEXT,
                secrets TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM owner_profile")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO owner_profile (id, name, aliases, preferences) VALUES (1, 'Infinite Vybeflix', 'Infinite, Vybeflix', '{}')")

        conn.commit()
        conn.close()

    def save_message(self, session_id, role, content, tool_calls=None, reasoning=None):
        conn = self.get_connection()
        conn.execute("INSERT INTO conversations (session_id, role, content, tool_calls, reasoning) VALUES (?, ?, ?, ?, ?)",
                    (session_id, role, content, json.dumps(tool_calls) if tool_calls else None, reasoning))
        conn.commit()
        conn.close()

    def get_conversation(self, session_id, limit=50):
        conn = self.get_connection()
        cursor = conn.execute("SELECT role, content, tool_calls, reasoning, created_at FROM conversations WHERE session_id = ? ORDER BY created_at DESC LIMIT ?", (session_id, limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def create_task(self, task_id, description, priority=5, estimated_duration=None):
        conn = self.get_connection()
        conn.execute("INSERT INTO tasks (task_id, description, priority, estimated_duration, status) VALUES (?, ?, ?, ?, 'pending')",
                    (task_id, description, priority, estimated_duration))
        conn.commit()
        conn.close()

    def update_task(self, task_id, status=None, steps=None, result=None, error=None):
        conn = self.get_connection()
        updates = []
        params = []
        if status:
            updates.append("status = ?")
            params.append(status)
            if status == "running":
                updates.append("started_at = CURRENT_TIMESTAMP")
            elif status in ("completed", "failed"):
                updates.append("completed_at = CURRENT_TIMESTAMP")
        if steps:
            updates.append("steps = ?")
            params.append(json.dumps(steps))
        if result:
            updates.append("result = ?")
            params.append(result)
        if error:
            updates.append("error = ?")
            params.append(error)
        if updates:
            params.append(task_id)
            conn.execute(f"UPDATE tasks SET {', '.join(updates)} WHERE task_id = ?", params)
            conn.commit()
        conn.close()

    def get_task(self, task_id):
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def save_memory(self, key, value, category="general", importance=5, source=None):
        conn = self.get_connection()
        conn.execute("INSERT INTO memory (key, value, category, importance, source) VALUES (?, ?, ?, ?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value, importance = excluded.importance, updated_at = CURRENT_TIMESTAMP",
                    (key, value, category, importance, source))
        conn.commit()
        conn.close()

    def get_memory(self, key):
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM memory WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def search_memory(self, query, category=None, limit=10):
        conn = self.get_connection()
        sql = "SELECT * FROM memory WHERE key LIKE ? OR value LIKE ?"
        params = [f"%{query}%", f"%{query}%"]
        if category:
            sql += " AND category = ?"
            params.append(category)
        sql += " ORDER BY importance DESC, updated_at DESC LIMIT ?"
        params.append(limit)
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_episode(self, event, context=None, emotion=None, lesson=None):
        conn = self.get_connection()
        conn.execute("INSERT INTO episodic_memory (event, context, emotion, lesson) VALUES (?, ?, ?, ?)", (event, context, emotion, lesson))
        conn.commit()
        conn.close()

    def get_episodes(self, limit=20):
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM episodic_memory ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def save_document(self, filename, original_name, file_type, file_size, content, summary=None, chunks=None, tags=None):
        conn = self.get_connection()
        conn.execute("INSERT INTO documents (filename, original_name, file_type, file_size, content, summary, chunks, tags) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (filename, original_name, file_type, file_size, content, summary, json.dumps(chunks) if chunks else None, tags))
        conn.commit()
        conn.close()

    def get_document(self, doc_id):
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def search_documents(self, query, limit=10):
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM documents WHERE content LIKE ? OR summary LIKE ? OR tags LIKE ? ORDER BY created_at DESC LIMIT ?",
                             (f"%{query}%", f"%{query}%", f"%{query}%", limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_owner(self, **kwargs):
        conn = self.get_connection()
        allowed = ["name", "aliases", "preferences", "personality_notes", "tech_stack_prefs", "project_history", "secrets"]
        updates = []
        params = []
        for k, v in kwargs.items():
            if k in allowed:
                updates.append(f"{k} = ?")
                params.append(json.dumps(v) if isinstance(v, (dict, list)) else v)
        if updates:
            params.append(1)
            conn.execute(f"UPDATE owner_profile SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", params)
            conn.commit()
        conn.close()

    def get_owner(self):
        conn = self.get_connection()
        cursor = conn.execute("SELECT * FROM owner_profile WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def log(self, level, component, message, stack_trace=None):
        conn = self.get_connection()
        conn.execute("INSERT INTO agent_logs (level, component, message, stack_trace) VALUES (?, ?, ?, ?)", (level, component, message, stack_trace))
        conn.commit()
        conn.close()

    def get_logs(self, level=None, component=None, limit=50):
        conn = self.get_connection()
        sql = "SELECT * FROM agent_logs WHERE 1=1"
        params = []
        if level:
            sql += " AND level = ?"
            params.append(level)
        if component:
            sql += " AND component = ?"
            params.append(component)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        cursor = conn.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

db = Database()
