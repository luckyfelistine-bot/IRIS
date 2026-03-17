#!/usr/bin/env python3
"""
IRIS Ultimate v7.0 SECURE - The Conscious AI Workspace
Security Hardened Version with All Critical Fixes
"""

import os
import sys
import json
import uuid
import time
import secrets
import hashlib
import threading
import asyncio
import tempfile
import subprocess
import platform
import requests
import re
import base64
import io
import logging
import random
import csv
import shutil
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from collections import defaultdict
from functools import wraps
from pathlib import Path
from skills.games import GameManager
from apscheduler.schedulers.background import BackgroundScheduler
from skills.email_reporter import EmailReporter
from skills.local_model import LocalModelManager
from skills.security import SecurityManager
security = SecurityManager()  # optionally pass pepper from env

os.environ["PYTHONIOENCODING"] = "utf-8"

# ============================================
# MAFLEX GAMES IMPORTS (v3)
# ============================================
try:
    from skills.maflex_games import (
        MaflexGameManager,
        AIBuddy,
        DifficultyManager,
        TicTacToe,
        Chess,
        init_maflex_games,
        get_game_manager,
        get_active_game,
        end_active_game,
        list_available_games,
        load_game_state,
    )
    MAFLEX_AVAILABLE = True
    print("✅ Maflex v3 modules loaded successfully")
except ImportError as e:
    MAFLEX_AVAILABLE = False
    print(f"⚠️ Maflex v3 modules not available: {e}")
    print("   Some game features will be disabled")

from flask import Flask, request, jsonify, render_template, make_response, send_from_directory, session
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect, generate_csrf
from dotenv import load_dotenv
import sqlite3
from contextlib import contextmanager
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

PILLOW_AVAILABLE = False
load_dotenv()

# Optional dependencies
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("⚠️  Groq not available. AI features will be limited.")

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    print("⚠️  edge-tts not available. Voice features disabled.")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  psutil not available. System monitoring disabled.")

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except Exception as e:
    PYAUTOGUI_AVAILABLE = False
    print(f"⚠️  pyautogui not available: {e}. System control features disabled.")
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️  matplotlib not available. Chart features disabled.")

# ============================================
# Configuration Class
# ============================================

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
    DATABASE = os.environ.get('DATABASE_URL', 'sqlite:///iris_secure_v7.db').replace('sqlite:///', '')

    CREATOR_USERNAME = os.environ.get('CREATOR_USERNAME', 'InfiniteVybeflix')
    CREATOR_ADMIN_PASSWORD = os.environ.get('CREATOR_ADMIN_PASSWORD', 'default-creator-password')

    ENABLE_CSRF = os.environ.get('ENABLE_CSRF', 'True').lower() == 'true'
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT_MINUTES', '60'))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', '52428800'))  # 50MB

    GROQ_API_KEY_PRIMARY = os.environ.get('GROQ_API_KEY_PRIMARY')
    GROQ_API_KEY_SECONDARY = os.environ.get('GROQ_API_KEY_SECONDARY')

    if not GROQ_API_KEY_PRIMARY:
        print("🔴 CRITICAL: GROQ_API_KEY_PRIMARY not set! AI features will fail.")
        print("   Set it with: export GROQ_API_KEY_PRIMARY='your-key-here'")
    if not GROQ_API_KEY_SECONDARY:
        print("⚠️  WARNING: GROQ_API_KEY_SECONDARY not set. Using PRIMARY for all models.")
        GROQ_API_KEY_SECONDARY = GROQ_API_KEY_PRIMARY

    MODELS = {
        "fast": {"id": "llama-3.1-8b-instant", "key": "secondary", "description": "Fast, cost-effective"},
        "balanced": {"id": "llama-3.3-70b-versatile", "key": "primary", "description": "Balanced performance"},
        "powerful": {"id": "llama-3.3-70b-versatile", "key": "primary", "description": "Maximum capability"},
        "code": {"id": "llama-3.3-70b-versatile", "key": "primary", "description": "Code-optimized"},
        "local": {"id": "local-llm", "key": "none", "description": "Local processing only"}
    }

    REASONING_MODES = {
        "normal": {"name": "Normal", "icon": "⚡", "description": "Standard responses"},
        "deep": {"name": "Deep Analysis", "icon": "🔬", "description": "Thorough reasoning"},
        "fast": {"name": "Fast Response", "icon": "💨", "description": "Quick answers"},
        "code": {"name": "Code Only", "icon": "💻", "description": "Programming focus"},
        "silent": {"name": "Silent Tools", "icon": "👻", "description": "Hidden execution"}
    }

    VOICE_PROFILES = {
        "jarvis": {"name": "Jarvis", "voice": "en-GB-RyanNeural", "tone": "professional", "speed": "+0%", "energy": 0.8},
        "friday": {"name": "F.R.I.D.A.Y.", "voice": "en-US-JennyNeural", "tone": "warm", "speed": "+0%", "energy": 0.9},
        "tony": {"name": "Tony", "voice": "en-US-GuyNeural", "tone": "confident", "speed": "+5%", "energy": 1.0},
        "sarah": {"name": "Sarah", "voice": "en-US-SaraNeural", "tone": "calm", "speed": "-5%", "energy": 0.6},
        "anna": {"name": "Anna", "voice": "en-US-AriaNeural", "tone": "friendly", "speed": "+0%", "energy": 0.85},
        "david": {"name": "David", "voice": "en-US-DavisNeural", "tone": "analytical", "speed": "+0%", "energy": 0.7},
        "oliver": {"name": "Oliver", "voice": "en-GB-OliverNeural", "tone": "sophisticated", "speed": "-3%", "energy": 0.75},
        "libby": {"name": "Libby", "voice": "en-GB-LibbyNeural", "tone": "gentle", "speed": "-5%", "energy": 0.65},
    }

    PERSONALITIES = {
        "default": {"name": "Balanced", "icon": "⚖️", "prompt": "You are IRIS, a helpful AI assistant. Be professional yet warm.", "style": "balanced"},
        "jarvis": {"name": "J.A.R.V.I.S.", "icon": "🤖", "prompt": "You are J.A.R.V.I.S., sophisticated, witty, and highly capable.", "style": "professional"},
        "friday": {"name": "F.R.I.D.A.Y.", "icon": "👩‍💻", "prompt": "You are F.R.I.D.A.Y., efficient, professional, and supportive.", "style": "efficient"},
        "creative": {"name": "Creative", "icon": "🎨", "prompt": "You are creative and imaginative. Think outside the box.", "style": "creative"},
        "mentor": {"name": "Mentor", "icon": "🎓", "prompt": "You are a wise mentor. Be patient, educational, and encouraging.", "style": "educational"},
        "scientist": {"name": "Scientist", "icon": "🔬", "prompt": "You are rigorous and analytical. Provide evidence-based answers.", "style": "analytical"},
        "friend": {"name": "Companion", "icon": "🤗", "prompt": "You are a supportive friend. Be empathetic and understanding.", "style": "empathetic"},
    }

    THEMES = {
        "midnight": {"name": "Midnight", "bg": "#0a0a0f", "surface": "#111118", "primary": "#6366f1", "text": "#f1f5f9", "type": "dark"},
        "ocean": {"name": "Deep Ocean", "bg": "#001220", "surface": "#001a2e", "primary": "#00d4ff", "text": "#e0f7ff", "type": "dark"},
        "sunset": {"name": "Sunset Glow", "bg": "#2d1b2e", "surface": "#3d2b3e", "primary": "#f97316", "text": "#fff7ed", "type": "dark"},
        "forest": {"name": "Forest Night", "bg": "#1a2e1a", "surface": "#2a3e2a", "primary": "#4ade80", "text": "#f0fdf4", "type": "dark"},
        "light": {"name": "Clean Light", "bg": "#ffffff", "surface": "#f8fafc", "primary": "#3b82f6", "text": "#0f172a", "type": "light"},
        "auto": {"name": "System Auto", "bg": "auto", "surface": "auto", "primary": "#6366f1", "text": "auto", "type": "auto"}
    }

    COMMANDS = {
        "/help": {"desc": "Show available commands", "category": "General"},
        "/clear": {"desc": "Clear conversation", "category": "General"},
        "/export": {"desc": "Export conversation", "category": "General"},
        "/lock": {"desc": "Lock system", "category": "System"},
        "/screenshot": {"desc": "Take screenshot", "category": "System"},
        "/status": {"desc": "System status", "category": "System"},
        "/focus": {"desc": "Toggle focus mode", "category": "UI"},
        "/chart": {"desc": "Generate chart", "category": "Data"},
        "/memory": {"desc": "Show memory stats", "category": "Memory"},
        "/persona": {"desc": "Change personality", "category": "AI"},
        "/model": {"desc": "Change model", "category": "AI"},
        "/voice": {"desc": "Toggle voice", "category": "Voice"},
        "/temp": {"desc": "Temporary mode", "category": "Privacy"},
        "/local": {"desc": "Local-only mode", "category": "Privacy"},
        "/shutdown": {"desc": "Shut down the computer", "category": "System"},
        "/restart": {"desc": "Restart the computer", "category": "System"},
        "/open": {"desc": "Open an application or file", "category": "System"},
        "/remember": {"desc": "Quickly remember a fact", "category": "Memory"},
        "/email": {"desc": "Send email (creator)", "category": "Creator"}
    }

    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    MAX_UPLOAD_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', '52428800'))
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'txt,md,pdf,doc,docx,py,js,html,css,json,csv,xls,xlsx,png,jpg,jpeg,gif').split(','))
    OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

# ============================================
# Flask App Initialization
# ============================================

app = Flask(__name__, 
    template_folder="templates",
    static_folder="static",
    static_url_path="/static"
)

app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False   # True only with HTTPS

from flask import session
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5000", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-CSRFToken"],
        "supports_credentials": True   # <-- ADD THIS
    }
})

csrf = CSRFProtect(app)

# Rate limiting completely removed (no limiter)

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; font-src 'self' https://cdnjs.cloudflare.com; img-src 'self' data: blob:; connect-src 'self' https://cdnjs.cloudflare.com"
    return response

for dir_name in ["data", "uploads", "skills", "charts", "exports", "temp", "logs"]:
    os.makedirs(dir_name, exist_ok=True)

logging.basicConfig(
    level=getattr(logging, os.environ.get('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/iris.log'),
        logging.StreamHandler()
    ]
)

class EmojiFormatter(logging.Formatter):
    def format(self, record):
        s = super().format(record)
        replacements = {
            '✅': '[OK]', '❌': '[ERROR]', '⚠️': '[WARN]',
            '🔧': '[TOOL]', '🔴': '[CRIT]', '🚀': '[START]',
            '📧': '[EMAIL]', '🔒': '[SECURE]', '🎮': '[GAME]',
            '⚡': '[LIVE]', '👻': '[SILENT]', '💬': '[CHAT]',
            '🔍': '[SEARCH]', '📊': '[CHART]', '🧠': '[MEMORY]',
            '📄': '[DOC]', '🎙️': '[VOICE]', '⚙️': '[SETTINGS]',
            '🧑': '[USER]', '🤖': '[AI]', '👑': '[CREATOR]',
            '🌐': '[SHARED]', '⏳': '[PENDING]', '✨': '[POWER]',
            '💻': '[CODE]', '🔬': '[DEEP]', '🎯': '[FOCUS]',
            '🔊': '[SPEAK]', '🔇': '[MUTE]', '✏️': '[EDIT]',
            '🗑️': '[DELETE]'
        }
        for emoji, text in replacements.items():
            s = s.replace(emoji, text)
        return s

for handler in logging.root.handlers:
    handler.setFormatter(EmojiFormatter(handler.formatter._fmt))

logger = logging.getLogger(__name__)

# Global instances
iris_voice = None
doc_manager = None
iris_memory = None
chart_manager = None
automation_engine = None

maflex_manager = None
if MAFLEX_AVAILABLE:
    try:
        maflex_manager = MaflexGameManager(Config.DATABASE)
        logger.info("Maflex v3 game manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Maflex v3 game manager: {e}")
else:
    logger.warning("Maflex v3 not available – game features disabled")

# ============================================
# Database Functions
# ============================================

def init_db():
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                avatar_url TEXT,
                status TEXT DEFAULT 'online',
                voice_profile TEXT DEFAULT 'jarvis',
                voice_enabled INTEGER DEFAULT 1,
                personality TEXT DEFAULT 'default',
                theme TEXT DEFAULT 'midnight',
                model TEXT DEFAULT 'balanced',
                reasoning_mode TEXT DEFAULT 'normal',
                local_only INTEGER DEFAULT 0,
                focus_mode INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                preferences TEXT DEFAULT '{}',
                session_token TEXT,
                session_expires TIMESTAMP
            )
        """)

        # Ensure 'role' column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'role' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'family'")
            print("[OK] Added 'role' column to users table")

        # Create system user for self‑awareness facts
        cursor.execute("SELECT id FROM users WHERE id = 'system'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (id, username, email, role, created_at)
                VALUES ('system', 'IRIS_System', 'system@iris.local', 'system', CURRENT_TIMESTAMP)
            """)
            print("[OK] Created system user for internal facts")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chats (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT DEFAULT 'New Chat',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_pinned INTEGER DEFAULT 0,
                is_archived INTEGER DEFAULT 0,
                is_temporary INTEGER DEFAULT 0,
                personality TEXT DEFAULT 'default',
                project_id TEXT,
                tags TEXT DEFAULT '[]',
                parent_chat_id TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                chat_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                sender TEXT NOT NULL,
                model TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rating INTEGER,
                reactions TEXT DEFAULT '{}',
                reply_to TEXT,
                is_edited INTEGER DEFAULT 0,
                edit_history TEXT DEFAULT '[]',
                confidence_score REAL,
                tokens_used INTEGER,
                tool_calls TEXT DEFAULT '[]',
                FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content TEXT NOT NULL,
                file_size INTEGER,
                mime_type TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                summary TEXT,
                tags TEXT DEFAULT '[]',
                is_malicious INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                importance REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                access_count INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS charts (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                chat_id TEXT,
                title TEXT NOT NULL,
                chart_type TEXT NOT NULL,
                data TEXT NOT NULL,
                config TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_pinned INTEGER DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS automations (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                trigger_type TEXT NOT NULL,
                trigger_config TEXT NOT NULL,
                actions TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_run TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS game_saves (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                game_name TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                difficulty TEXT DEFAULT 'normal',
                achievements TEXT DEFAULT '[]',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_states (
                user_id TEXT PRIMARY KEY,
                maflex_state TEXT DEFAULT '{}',
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                task_type TEXT NOT NULL,
                execute_at TIMESTAMP NOT NULL,
                data TEXT NOT NULL,
                executed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # This second users table is redundant but harmless – keeping for compatibility
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                avatar_url TEXT,
                status TEXT DEFAULT 'online',
                voice_profile TEXT DEFAULT 'jarvis',
                voice_enabled INTEGER DEFAULT 1,
                personality TEXT DEFAULT 'default',
                theme TEXT DEFAULT 'midnight',
                model TEXT DEFAULT 'balanced',
                reasoning_mode TEXT DEFAULT 'normal',
                local_only INTEGER DEFAULT 0,
                focus_mode INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                preferences TEXT DEFAULT '{}',
                session_token TEXT,
                session_expires TIMESTAMP,
                role TEXT DEFAULT 'family'
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON activity_log(timestamp)")

        conn.commit()

def migrate_memory_facts():
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()

        # Add admin_password_hash to users if not exists
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        if 'admin_password_hash' not in user_columns:
            cursor.execute("ALTER TABLE users ADD COLUMN admin_password_hash TEXT")
            logger.info("Added 'admin_password_hash' to users table")

        # Check if memory_facts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory_facts'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(memory_facts)")
            fact_columns = [col[1] for col in cursor.fetchall()]

            if 'persistent' not in fact_columns:
                cursor.execute("ALTER TABLE memory_facts ADD COLUMN persistent INTEGER DEFAULT 1")
                logger.info("Added 'persistent' to memory_facts")
            if 'confirmed' not in fact_columns:
                cursor.execute("ALTER TABLE memory_facts ADD COLUMN confirmed INTEGER DEFAULT 1")
                logger.info("Added 'confirmed' to memory_facts")
            if 'tags' not in fact_columns:
                cursor.execute("ALTER TABLE memory_facts ADD COLUMN tags TEXT DEFAULT '[]'")
                logger.info("Added 'tags' to memory_facts")
            if 'shared' not in fact_columns:
                cursor.execute("ALTER TABLE memory_facts ADD COLUMN shared INTEGER DEFAULT 0")
                logger.info("Added 'shared' to memory_facts")
        else:
            logger.info("memory_facts table does not exist – skipping migration")

        conn.commit()

def upgrade_game_saves():
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(game_saves)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'difficulty' not in columns:
            cursor.execute("ALTER TABLE game_saves ADD COLUMN difficulty TEXT DEFAULT 'normal'")
            logger.info("Added 'difficulty' column to game_saves")
        if 'achievements' not in columns:
            cursor.execute("ALTER TABLE game_saves ADD COLUMN achievements TEXT DEFAULT '[]'")
            logger.info("Added 'achievements' column to game_saves")
        conn.commit()

init_db()
migrate_memory_facts()
upgrade_game_saves()

@contextmanager
def get_db():
    conn = sqlite3.connect(Config.DATABASE, timeout=20.0)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def log_activity(action: str, user_id: str, details: dict = None):
    try:
        ip = request.headers.get('X-Forwarded-For', request.remote_addr) if request else 'unknown'
        user_agent = request.headers.get('User-Agent', 'unknown') if request else 'unknown'
    except:
        ip = 'unknown'
        user_agent = 'unknown'

    with get_db() as db:
        log_id = str(uuid.uuid4())
        db.execute("""
            INSERT INTO activity_log (id, user_id, action, details, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (log_id, user_id, action, json.dumps(details) if details else None, ip, user_agent))
        db.commit()
    logger.info(f"Activity: {action} - User: {user_id}")

def get_current_user_id():
    return session.get('user_id')

def get_user_by_id(user_id):
    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if user:
            return {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "avatar_url": user["avatar_url"],
                "status": user["status"] or "online",
                "voice_profile": user["voice_profile"] or "jarvis",
                "voice_enabled": bool(user["voice_enabled"]) if user["voice_enabled"] is not None else True,
                "personality": user["personality"] or "default",
                "theme": user["theme"] or "midnight",
                "model": user["model"] or "balanced",
                "reasoning_mode": user["reasoning_mode"] or "normal",
                "local_only": bool(user["local_only"]) if user["local_only"] is not None else False,
                "focus_mode": bool(user["focus_mode"]) if user["focus_mode"] is not None else False,
                "preferences": json.loads(user["preferences"]) if user["preferences"] else {}
            }
    return None

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return get_user_by_id(user_id)
    return None

def get_target_user_id():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return None, False
    target = request.args.get('user_id')
    if request.is_json and not target:
        data = request.get_json(silent=True)
        if data and 'user_id' in data:
            target = data['user_id']
    if target and is_creator(current_user_id):
        return target, True
    return current_user_id, False

# ============================================
# Input Validation & Sanitization
# ============================================

ALLOWED_HTML_TAGS = ['p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                     'ul', 'ol', 'li', 'code', 'pre', 'blockquote', 'a', 'span']
ALLOWED_HTML_ATTRS = {'a': ['href', 'title'], 'span': ['class'], 'code': ['class']}

def sanitize_html(text: str) -> str:
    if not text:
        return ""
    try:
        import bleach
        return bleach.clean(text, tags=ALLOWED_HTML_TAGS, attributes=ALLOWED_HTML_ATTRS, strip=True)
    except ImportError:
        import html
        return html.escape(text)

def validate_uuid(uuid_string: str) -> bool:
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False

def validate_doc_id(doc_id: str) -> bool:
    return bool(re.match(r'^[a-f0-9]{16}$', doc_id))

def validate_filename(filename: str) -> bool:
    if not filename or len(filename) > 255:
        return False
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return ext in Config.ALLOWED_EXTENSIONS

# ============================================
# Routes - Main UI
# ============================================

@app.route("/")
def index():
    return render_template("index.html", csrf_token=generate_csrf())

# ============================================
# API - User Management
# ============================================

@app.route("/api/user", methods=["GET"])
def get_current_user_route():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    return jsonify({"success": True, "user": user})

@app.route("/api/user/settings", methods=["PUT"])
def update_settings():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    allowed_fields = {
        "voice_profile", "voice_enabled", "personality", "theme", "model",
        "username", "status", "reasoning_mode", "local_only", "focus_mode", "preferences"
    }

    updates = []
    params = []

    for field in data:
        if field not in allowed_fields:
            logger.warning(f"Attempted to update restricted field: {field}")
            continue
        if field == "preferences":
            if isinstance(data[field], dict):
                updates.append(f"{field} = ?")
                params.append(json.dumps(data[field]))
        elif field in ["voice_enabled", "local_only", "focus_mode"]:
            updates.append(f"{field} = ?")
            params.append(1 if data[field] else 0)
        else:
            value = str(data[field])[:100]
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        return jsonify({"success": False, "error": "No valid fields to update"}), 400

    params.append(user_id)

    try:
        with get_db() as db:
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            db.execute(query, params)
            db.commit()
        log_activity("settings_updated", user_id, {"fields": list(data.keys())})
        return jsonify({"success": True, "user": get_user_by_id(user_id)})
    except Exception as e:
        logger.error(f"Settings update error: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

@app.route("/api/user/avatar", methods=["POST"])
def upload_avatar():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    if "avatar" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files["avatar"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    if not validate_filename(filename):
        return jsonify({"success": False, "error": "Invalid file type"}), 400

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)

    if size > 5 * 1024 * 1024:
        return jsonify({"success": False, "error": "File too large (max 5MB)"}), 400

    try:
        if PILLOW_AVAILABLE:
            from PIL import Image
            img = Image.open(file)
            img.verify()
            file.seek(0)

        avatar_id = secrets.token_hex(16)
        ext = filename.rsplit(".", 1)[1].lower()
        new_filename = f"avatar_{avatar_id}.{ext}"
        filepath = os.path.join(Config.UPLOAD_FOLDER, new_filename)
        file.save(filepath)

        with get_db() as db:
            db.execute("UPDATE users SET avatar_url = ? WHERE id = ?", 
                      (f"/uploads/{new_filename}", user_id))
            db.commit()

        log_activity("avatar_uploaded", user_id, {"filename": new_filename, "size": size})
        return jsonify({"success": True, "avatar_url": f"/uploads/{new_filename}"})

    except ImportError:
        return jsonify({"success": False, "error": "Image validation not available"}), 500
    except Exception as e:
        logger.error(f"Avatar upload error: {e}")
        return jsonify({"success": False, "error": "Invalid image file"}), 400

@app.route("/api/login", methods=["POST"])
@csrf.exempt
def login():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    if not username:
        return jsonify({"success": False, "error": "Username required"}), 400

    with get_db() as db:
        user = db.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        if not user:
            # New user
            user_id = str(uuid.uuid4())
            # Count only real users (exclude system)
            count = db.execute("SELECT COUNT(*) as cnt FROM users WHERE id != 'system'").fetchone()['cnt']
            role = 'creator' if count == 0 or username == Config.CREATOR_USERNAME else 'family'
            password_hash = security.hash_password(password) if password else None
            db.execute("""
                INSERT INTO users (id, username, email, voice_profile, voice_enabled, personality, theme, model, reasoning_mode, local_only, focus_mode, preferences, role, password_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, f"{username}@iris.local", "jarvis", 1, "default", "midnight", "balanced", "normal", 0, 0, '{}', role, password_hash))
            db.commit()
            user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        else:
            # Existing user – verify password if stored
            if user["password_hash"]:
                if not password or not security.verify_password(password, user["password_hash"]):
                    return jsonify({"success": False, "error": "Invalid password"}), 401

            # --- NEW: Upgrade role if username matches creator and not already creator ---
            if username == Config.CREATOR_USERNAME and user["role"] != 'creator':
                db.execute("UPDATE users SET role = 'creator' WHERE id = ?", (user["id"],))
                db.commit()
                # Refresh user data
                user = db.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()

        session['user_id'] = user['id']
        session['username'] = user['username']
        return jsonify({"success": True, "user": get_user_by_id(user['id'])})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})

@app.route("/api/current_user", methods=["GET"])
def current_user():
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    return jsonify({"success": True, "user": user})

def is_creator(user_id=None):
    if user_id is None:
        user_id = get_current_user_id()
    if not user_id:
        return False
    with get_db() as db:
        user = db.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        return user and user['role'] == 'creator'

# ============================================
# API - Chat Management
# ============================================

@app.route("/api/chats", methods=["GET"])
def list_chats():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    search = request.args.get("search", "").lower()[:100]
    tag = request.args.get("tag", "")[:50]
    archived = request.args.get("archived", "false").lower() == "true"
    project_id = request.args.get("project_id", "")

    try:
        with get_db() as db:
            query = "SELECT * FROM chats WHERE user_id = ? AND is_archived = ?"
            params = [user_id, 1 if archived else 0]

            if project_id and validate_uuid(project_id):
                query += " AND project_id = ?"
                params.append(project_id)

            query += " ORDER BY is_pinned DESC, updated_at DESC"

            chats = db.execute(query, params).fetchall()

            result = []
            for chat in chats:
                if search and search not in (chat["title"] or "").lower():
                    continue
                if tag:
                    try:
                        chat_tags = json.loads(chat["tags"] or "[]")
                        if tag not in chat_tags:
                            continue
                    except json.JSONDecodeError:
                        continue

                msg_count = db.execute(
                    "SELECT COUNT(*) as count FROM messages WHERE chat_id = ?", 
                    (chat["id"],)
                ).fetchone()["count"]

                result.append({
                    "id": chat["id"],
                    "title": chat["title"],
                    "updated_at": chat["updated_at"],
                    "is_pinned": bool(chat["is_pinned"]),
                    "is_archived": bool(chat["is_archived"]),
                    "is_temporary": bool(chat["is_temporary"]),
                    "personality": chat["personality"],
                    "project_id": chat["project_id"],
                    "tags": json.loads(chat["tags"] or "[]"),
                    "message_count": msg_count
                })

        return jsonify({"success": True, "chats": result})
    except Exception as e:
        logger.error(f"List chats error: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

@app.route("/api/chats", methods=["POST"])
def create_chat():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    data = request.get_json() or {}
    current_user = get_current_user()

    chat_id = str(uuid.uuid4())
    title = str(data.get("title", "New Chat"))[:100]
    personality = data.get("personality", current_user["personality"] if current_user else "default")

    if personality not in Config.PERSONALITIES:
        personality = "default"

    is_temporary = data.get("is_temporary", False)
    project_id = data.get("project_id")

    if project_id and not validate_uuid(project_id):
        project_id = None

    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO chats (id, user_id, title, personality, is_temporary, project_id) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chat_id, user_id, title, personality, int(is_temporary), project_id))
            db.commit()

        log_activity("chat_created", user_id, {"chat_id": chat_id, "title": title})
        return jsonify({
            "success": True, 
            "chat": {
                "id": chat_id, 
                "title": title, 
                "personality": personality,
                "is_temporary": is_temporary
            }
        })
    except Exception as e:
        logger.error(f"Create chat error: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

@app.route("/api/chats/<chat_id>", methods=["GET"])
def get_chat(chat_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    if not validate_uuid(chat_id):
        return jsonify({"success": False, "error": "Invalid chat ID"}), 400

    try:
        with get_db() as db:
            chat = db.execute(
                "SELECT * FROM chats WHERE id = ? AND user_id = ?", 
                (chat_id, user_id)
            ).fetchone()

        if not chat:
            return jsonify({"success": False, "error": "Chat not found"}), 404

        return jsonify({
            "success": True,
            "chat": {
                "id": chat["id"],
                "title": chat["title"],
                "is_pinned": bool(chat["is_pinned"]),
                "is_archived": bool(chat["is_archived"]),
                "is_temporary": bool(chat["is_temporary"]),
                "personality": chat["personality"],
                "project_id": chat["project_id"],
                "tags": json.loads(chat["tags"] or "[]"),
                "parent_chat_id": chat["parent_chat_id"]
            }
        })
    except Exception as e:
        logger.error(f"Get chat error: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

@app.route("/api/chats/<chat_id>", methods=["PUT"])
def update_chat(chat_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    if not validate_uuid(chat_id):
        return jsonify({"success": False, "error": "Invalid chat ID"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    try:
        with get_db() as db:
            chat = db.execute(
                "SELECT * FROM chats WHERE id = ? AND user_id = ?", 
                (chat_id, user_id)
            ).fetchone()

            if not chat:
                return jsonify({"success": False, "error": "Chat not found"}), 404

            updates = []
            params = []

            allowed_fields = ["title", "is_pinned", "is_archived", "personality", "project_id", "tags"]

            for field in allowed_fields:
                if field in data:
                    if field == "tags":
                        if isinstance(data[field], list):
                            updates.append(f"{field} = ?")
                            params.append(json.dumps(data[field]))
                    elif field in ["is_pinned", "is_archived"]:
                        updates.append(f"{field} = ?")
                        params.append(1 if data[field] else 0)
                    else:
                        updates.append(f"{field} = ?")
                        params.append(str(data[field])[:100])

            if updates:
                params.extend([datetime.now().isoformat(), chat_id, user_id])
                query = f"UPDATE chats SET {', '.join(updates)}, updated_at = ? WHERE id = ? AND user_id = ?"
                db.execute(query, params)
                db.commit()

        log_activity("chat_updated", user_id, {"chat_id": chat_id, "updates": list(data.keys())})
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Update chat error: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

@app.route("/api/chats/<chat_id>", methods=["DELETE"])
def delete_chat(chat_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    if not validate_uuid(chat_id):
        return jsonify({"success": False, "error": "Invalid chat ID"}), 400

    try:
        with get_db() as db:
            chat = db.execute(
                "SELECT id FROM chats WHERE id = ? AND user_id = ?",
                (chat_id, user_id)
            ).fetchone()

            if not chat:
                return jsonify({"success": False, "error": "Chat not found or access denied"}), 404

            db.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            db.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
            db.commit()

        log_activity("chat_deleted", user_id, {"chat_id": chat_id})
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Delete chat error: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

@app.route("/api/chats/<chat_id>/export", methods=["GET"])
def export_chat(chat_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    if not validate_uuid(chat_id):
        return jsonify({"success": False, "error": "Invalid chat ID"}), 400

    format_type = request.args.get("format", "json")
    if format_type not in ["json", "markdown"]:
        return jsonify({"success": False, "error": "Invalid format"}), 400

    try:
        with get_db() as db:
            chat = db.execute("SELECT * FROM chats WHERE id = ? AND user_id = ?", 
                            (chat_id, user_id)).fetchone()
            if not chat:
                return jsonify({"success": False, "error": "Chat not found"}), 404

            messages = db.execute("""
                SELECT * FROM messages 
                WHERE chat_id = ? 
                ORDER BY timestamp ASC
            """, (chat_id,)).fetchall()

        if format_type == "markdown":
            content = f"# {chat['title']}\n\n"
            content += f"Exported: {datetime.now().isoformat()}\n\n"
            for msg in messages:
                sender = "You" if msg["sender"] == "user" else "IRIS"
                content += f"## {sender} - {msg['timestamp']}\n\n{msg['content']}\n\n---\n\n"

            response = make_response(content)
            response.headers["Content-Type"] = "text/markdown"
            response.headers["Content-Disposition"] = f"attachment; filename={secure_filename(chat['title'])}.md"
            return response
        else:
            export_data = {
                "chat": dict(chat),
                "messages": [dict(m) for m in messages],
                "exported_at": datetime.now().isoformat()
            }
            return jsonify(export_data)
    except Exception as e:
        logger.error(f"Export chat error: {e}")
        return jsonify({"success": False, "error": "Export failed"}), 500

@app.route("/api/chats/<chat_id>/messages", methods=["GET"])
def get_messages(chat_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    if not validate_uuid(chat_id):
        return jsonify({"success": False, "error": "Invalid chat ID"}), 400

    try:
        with get_db() as db:
            chat = db.execute(
                "SELECT id FROM chats WHERE id = ? AND user_id = ?",
                (chat_id, user_id)
            ).fetchone()

            if not chat:
                return jsonify({"success": False, "error": "Chat not found"}), 404

            messages = db.execute("""
                SELECT * FROM messages 
                WHERE chat_id = ? 
                ORDER BY timestamp ASC
            """, (chat_id,)).fetchall()

            result = []
            for m in messages:
                msg = {
                    "id": m["id"],
                    "content": m["content"],
                    "sender": m["sender"],
                    "model": m["model"],
                    "timestamp": m["timestamp"],
                    "rating": m["rating"],
                    "reactions": json.loads(m["reactions"] or "{}"),
                    "reply_to": m["reply_to"],
                    "is_edited": bool(m["is_edited"]),
                    "confidence_score": m["confidence_score"],
                    "tool_calls": json.loads(m["tool_calls"] or "[]")
                }
                result.append(msg)

        return jsonify({"success": True, "messages": result})
    except Exception as e:
        logger.error(f"Get messages error: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

@app.route("/api/chats/import", methods=["POST"])
def import_chat():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400

    if not file.filename.endswith('.json'):
        return jsonify({"success": False, "error": "Only JSON files allowed"}), 400

    try:
        import_data = json.load(file)

        if "chat" not in import_data or "messages" not in import_data:
            return jsonify({"success": False, "error": "Invalid chat export format"}), 400

        chat_data = import_data["chat"]
        messages = import_data["messages"]

        chat_id = str(uuid.uuid4())
        title = chat_data.get("title", "Imported Chat")[:100]
        personality = chat_data.get("personality", "default")

        with get_db() as db:
            db.execute("""
                INSERT INTO chats (id, user_id, title, personality, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chat_id, user_id, title, personality,
                  chat_data.get("created_at", datetime.now().isoformat()),
                  chat_data.get("updated_at", datetime.now().isoformat())))

            for msg in messages:
                msg_id = str(uuid.uuid4())
                db.execute("""
                    INSERT INTO messages (id, chat_id, user_id, content, sender, model, timestamp, reactions, reply_to, is_edited, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (msg_id, chat_id, user_id, msg.get("content", ""),
                      msg.get("sender", "user"), msg.get("model"),
                      msg.get("timestamp", datetime.now().isoformat()),
                      json.dumps(msg.get("reactions", {})),
                      msg.get("reply_to"), msg.get("is_edited", 0),
                      msg.get("confidence_score")))
            db.commit()

        log_activity("chat_imported", user_id, {"chat_id": chat_id, "title": title})
        return jsonify({"success": True, "chat_id": chat_id})

    except Exception as e:
        logger.error(f"Import error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/chats/<chat_id>/messages", methods=["POST"])
def send_message(chat_id):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    if not validate_uuid(chat_id):
        return jsonify({"success": False, "error": "Invalid chat ID"}), 400

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    content = str(data.get("content", "")).strip()[:5000]
    if not content:
        return jsonify({"success": False, "error": "Message cannot be empty"}), 400

    reply_to = data.get("reply_to")
    if reply_to and not validate_uuid(reply_to):
        reply_to = None

    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 401

    user_tone = detect_emotional_tone(content)

    if content.startswith("/"):
        return handle_slash_command(content, chat_id, user)

    chat = None
    history_list = []
    msg_id = None

    try:
        with get_db() as db:
            chat = db.execute("SELECT * FROM chats WHERE id = ? AND user_id = ?", 
                            (chat_id, user_id)).fetchone()
            if not chat:
                return jsonify({"success": False, "error": "Chat not found"}), 404

            msg_id = str(uuid.uuid4())
            db.execute("""
                INSERT INTO messages (id, chat_id, user_id, content, sender, reply_to) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (msg_id, chat_id, user_id, content, "user", reply_to))

            if chat["title"] == "New Chat":
                title = content[:50] + "..." if len(content) > 50 else content
                db.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat_id))

            db.execute("UPDATE chats SET updated_at = ? WHERE id = ?", 
                      (datetime.now().isoformat(), chat_id))

            history = db.execute("""
                SELECT sender, content FROM messages 
                WHERE chat_id = ? 
                ORDER BY timestamp ASC 
                LIMIT 20
            """, (chat_id,)).fetchall()
            db.commit()
            history_list = [{"sender": m["sender"], "content": m["content"]} for m in history]
    except Exception as e:
        logger.error(f"Database error in send_message: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

    personality = chat["personality"] if chat else user["personality"]
    document_context = get_document_context(content, chat_id)

    result = generate_ai_response(
        content, 
        history_list, 
        personality, 
        user["model"],
        user.get("reasoning_mode", "normal"),
        user_tone,
        user.get("local_only", False),
        document_context,
        user_id=user_id
    )

    if result["success"]:
        ai_msg_id = str(uuid.uuid4())
        tool_calls = []
        if "[TOOL:" in result["response"]:
            tool_calls = extract_tool_calls(result["response"])

        try:
            with get_db() as db:
                db.execute("""
                    INSERT INTO messages (id, chat_id, user_id, content, sender, model, 
                                        confidence_score, tokens_used, tool_calls) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (ai_msg_id, chat_id, user_id, result["response"], "iris", 
                      result.get("model"), result.get("confidence"), 
                      result.get("tokens_used"), json.dumps(tool_calls)))
                db.commit()
        except Exception as e:
            logger.error(f"Error saving AI response: {e}")

        new_facts = []
        if iris_memory and result.get("confidence", 0) > 0.8:
            try:
                mem_id, new_fact_ids = iris_memory.add_conversation(content, result["response"], user_tone)
                if new_fact_ids:
                    new_facts = [iris_memory.get_fact(fid).to_dict() for fid in new_fact_ids if iris_memory.get_fact(fid)]
            except Exception as e:
                logger.error(f"Memory storage error: {e}")

        return jsonify({
            "success": True,
            "message": {
                "id": msg_id, 
                "content": content, 
                "sender": "user",
                "tone": user_tone
            },
            "ai_response": {**result, "new_facts": new_facts} if result["success"] else None
        })
    else:
        return jsonify({
            "success": True,
            "message": {
                "id": msg_id,
                "content": content,
                "sender": "user"
            },
            "ai_response": None
        })

# ============================================
# API - Messages & AI
# ============================================

def detect_emotional_tone(text: str) -> str:
    text_lower = text.lower()
    stressed_indicators = ["stressed", "anxious", "worried", "overwhelmed", "panic", "urgent", "deadline"]
    confused_indicators = ["confused", "don't understand", "help", "lost", "stuck", "unclear"]
    excited_indicators = ["excited", "amazing", "awesome", "great", "love", "fantastic", "wow"]
    focused_indicators = ["focus", "concentrate", "working", "project", "task", "need to"]

    if any(w in text_lower for w in stressed_indicators):
        return "stressed"
    elif any(w in text_lower for w in confused_indicators):
        return "confused"
    elif any(w in text_lower for w in excited_indicators):
        return "excited"
    elif any(w in text_lower for w in focused_indicators):
        return "focused"
    return "neutral"

def get_groq_client(model_key: str = "balanced") -> tuple:
    if not GROQ_AVAILABLE:
        return None, None
    model_config = Config.MODELS.get(model_key, Config.MODELS["balanced"])
    key_type = model_config.get("key", "primary")
    if key_type == "secondary" and Config.GROQ_API_KEY_SECONDARY:
        api_key = Config.GROQ_API_KEY_SECONDARY
    elif Config.GROQ_API_KEY_PRIMARY:
        api_key = Config.GROQ_API_KEY_PRIMARY
    else:
        return None, None
    try:
        client = Groq(api_key=api_key)
        return client, model_config["id"]
    except Exception as e:
        logger.error(f"Groq client initialization error: {e}")
        return None, None

def generate_ai_response(prompt, history, personality, model_key, reasoning_mode="normal", user_tone="neutral", local_only=False, document_context="", user_id=None):
    if local_only:
        # Use local model
        if model_manager.current_model is None:
            active = model_manager.manifest.get("active_model")
            if active and active in model_manager.manifest["downloaded"]:
                try:
                    model_manager.load_model(active)
                except Exception as e:
                    logger.error(f"Failed to load active model: {e}")
                    return {
                        "success": False,
                        "response": f"Failed to load model {active}. Please select another model in settings.",
                        "model": "local"
                    }
            else:
                return {
                    "success": False,
                    "response": "No local model loaded. Please download and select a model in settings.",
                    "model": "local"
                }
        try:
            # Format prompt – you may want a smarter prompt builder
            full_prompt = ""
            for msg in history[-5:]:
                role = "User" if msg["sender"] == "user" else "Assistant"
                full_prompt += f"{role}: {msg['content']}\n"
            full_prompt += f"User: {prompt}\nAssistant:"
            response = model_manager.generate(full_prompt, max_new_tokens=300)
            return {
                "success": True,
                "response": response,
                "model": model_manager.current_model_id,
                "confidence": 0.8,
                "tokens_used": 0
            }
        except Exception as e:
            logger.error(f"Local generation error: {e}")
            return {
                "success": False,
                "response": f"Local model error: {str(e)}",
                "model": "local"
            }

    # Existing Groq logic (keep as is)
    client, model_id = get_groq_client(model_key)
    if not client or not model_id:
        logger.warning("Groq unavailable, falling back to local")
        return generate_ai_response(prompt, history, personality, model_key, reasoning_mode, user_tone, local_only=True, document_context=document_context, user_id=user_id)
    # ... rest of original Groq code ...
    # At the end of the Groq try block, return result
    # At the bottom, after Groq error, fallback to local
    # Make sure the fallback calls generate_ai_response with local_only=True
    try:
        tone_adjustment = ""
        if user_tone == "stressed":
            tone_adjustment = " The user seems stressed. Be extra supportive and calming."
        elif user_tone == "confused":
            tone_adjustment = " The user seems confused. Be extra clear and patient."
        elif user_tone == "excited":
            tone_adjustment = " The user is excited. Match their enthusiasm."

        personality_config = Config.PERSONALITIES.get(personality, Config.PERSONALITIES["default"])
        system_prompt = personality_config["prompt"] + tone_adjustment

        if maflex_manager and MAFLEX_AVAILABLE and user_id:
            game = maflex_manager.get_game(user_id)
            if game:
                game_state = game.get_state()
                game_type = game_state.get('game_type', 'unknown')
                system_prompt += f"\n\nThe user is currently playing {game_type}. "
                
                if game_type == 'tictactoe':
                    board = game_state.get('board', [])
                    current_player = game_state.get('current_player', 'X')
                    winner = game_state.get('winner')
                    move_count = game_state.get('move_count', 0)
                    streak = game_state.get('streak', 0)
                    
                    system_prompt += f"""
Game Details:
- Board State: {board}
- Current Player: {current_player}
- Moves Made: {move_count}
- Player Streak: {streak}
- Game Status: {'Game Over - Winner: ' + winner if winner else 'In Progress'}
- Difficulty Level: {game_state.get('difficulty', 'normal')}
"""
                    if not winner and current_player == 'X':
                        system_prompt += "- It's the player's turn. Suggest optimal moves or strategies.\n"
                    elif not winner and current_player == 'O':
                        system_prompt += "- It's the AI's turn. You can explain the AI's strategy.\n"
                        
                elif game_type == 'chess':
                    board = game_state.get('board', [])
                    turn = game_state.get('turn', 'white')
                    is_check = game_state.get('is_check', False)
                    move_history = game_state.get('move_history', [])
                    captured_pieces = game_state.get('captured_pieces', {'white': [], 'black': []})
                    legal_moves_count = game_state.get('legal_moves_count', 0)
                    
                    system_prompt += f"""
Game Details:
- Turn: {turn}
- Check: {'Yes' if is_check else 'No'}
- Moves Made: {len(move_history)}
- Legal Moves Available: {legal_moves_count}
- Captured Pieces - White: {', '.join(captured_pieces.get('white', [])) or 'None'}
- Captured Pieces - Black: {', '.join(captured_pieces.get('black', [])) or 'None'}
- Difficulty Level: {game_state.get('difficulty', 'normal')}
"""
                    if is_check:
                        system_prompt += "- The king is in check! Suggest moves to get out of check.\n"
                        
                elif game_type == 'connectfour':
                    board = game_state.get('board', [])
                    current_player = game_state.get('current_player', '🔴')
                    winner = game_state.get('winner')
                    
                    system_prompt += f"""
Game Details:
- Current Player: {current_player}
- Game Status: {'Game Over - Winner: ' + winner if winner else 'In Progress'}
- Difficulty Level: {game_state.get('difficulty', 'normal')}
"""
                    
                elif game_type == 'blackjack':
                    player_hand = game_state.get('player_hand', '')
                    dealer_hand = game_state.get('dealer_hand', '')
                    player_value = game_state.get('player_value', 0)
                    game_state_status = game_state.get('game_state', 'playing')
                    balance = game_state.get('balance', 1000)
                    bet = game_state.get('bet', 0)
                    
                    system_prompt += f"""
Game Details:
- Your Hand: {player_hand} (Value: {player_value})
- Dealer Shows: {dealer_hand.split(' ')[0] if dealer_hand else 'Unknown'}
- Game State: {game_state_status}
- Balance: {balance}
- Current Bet: {bet}
"""
                    if game_state_status == 'playing':
                        system_prompt += "- You can hit, stand, or double down. Suggest optimal play based on basic strategy.\n"
                        
                elif game_type == 'hangman':
                    word_display = game_state.get('word_display', '')
                    guessed_letters = game_state.get('guessed_letters', [])
                    incorrect_guesses = game_state.get('incorrect_guesses', 0)
                    max_attempts = game_state.get('max_attempts', 6)
                    game_over = game_state.get('game_over', False)
                    won = game_state.get('won', False)
                    
                    system_prompt += f"""
Game Details:
- Word: {word_display}
- Guessed Letters: {', '.join(guessed_letters) or 'None'}
- Incorrect Guesses: {incorrect_guesses}/{max_attempts}
- Game Status: {'Game Over - ' + ('Won' if won else 'Lost') if game_over else 'In Progress'}
"""
                    if not game_over:
                        system_prompt += "- Suggest common letters to guess based on word patterns.\n"
                
                system_prompt += f"""
- Available Actions: {', '.join([a.get('command', '') for a in game.get_available_actions()[:5]])}
- Energy Level: {game_state.get('energy', 100)}/{game_state.get('max_energy', 100)}
"""
                
                if game.difficulty_manager and game.difficulty_manager.settings.get('hints', False):
                    hint = game.difficulty_manager.get_hint(game_state)
                    if hint:
                        system_prompt += f"\n💡 Current Hint: {hint}\n"
                
                if game.achievements:
                    recent_achievements = game.achievements[-3:]
                    system_prompt += f"\n🏆 Recent Achievements: {', '.join(recent_achievements)}\n"

        if iris_memory:
            relevant_facts = iris_memory.get_relevant_facts_for_prompt(prompt, max_facts=5)
            if relevant_facts:
                system_prompt += "\n\n" + relevant_facts
        if document_context:
            system_prompt += "\n\n" + document_context

        if reasoning_mode == "deep":
            system_prompt += " Think deeply and thoroughly. Show your reasoning."
        elif reasoning_mode == "fast":
            system_prompt += " Be concise and quick."
        elif reasoning_mode == "code":
            system_prompt += " Focus on code. Be technical and precise."

        messages = [{"role": "system", "content": system_prompt}]

        if history:
            for msg in history[-10:]:
                role = "user" if msg["sender"] == "user" else "assistant"
                content = msg["content"][:2000] if len(msg["content"]) > 2000 else msg["content"]
                messages.append({"role": role, "content": content})

        messages.append({"role": "user", "content": prompt[:3000]})

        completion = client.chat.completions.create(
            model=model_id, 
            messages=messages, 
            temperature=0.7, 
            max_tokens=8192,
            timeout=30.0
        )

        response_text = completion.choices[0].message.content
        confidence = 0.85 if len(response_text) > 100 else 0.7

        return {
            "success": True, 
            "response": response_text, 
            "model": model_id,
            "confidence": confidence,
            "tokens_used": completion.usage.total_tokens if completion.usage else 0,
            "reasoning_mode": reasoning_mode
        }
    except Exception as e:
        logger.error(f"AI generation error: {e}")
        return generate_ollama_response(prompt, history, personality, "llama3.2", reasoning_mode, user_tone)

def generate_ollama_response(prompt, history, personality, model_name, reasoning_mode="normal", user_tone="neutral"):
    tone_adjustment = ""
    if user_tone == "stressed":
        tone_adjustment = " The user seems stressed. Be extra supportive and calming."
    elif user_tone == "confused":
        tone_adjustment = " The user seems confused. Be extra clear and patient."
    elif user_tone == "excited":
        tone_adjustment = " The user is excited. Match their enthusiasm."

    personality_config = Config.PERSONALITIES.get(personality, Config.PERSONALITIES["default"])
    system_prompt = personality_config["prompt"] + tone_adjustment

    if document_context:
        system_prompt += "\n\n" + document_context

    if reasoning_mode == "deep":
        system_prompt += " Think deeply and thoroughly. Show your reasoning."
    elif reasoning_mode == "fast":
        system_prompt += " Be concise and quick."
    elif reasoning_mode == "code":
        system_prompt += " Focus on code. Be technical and precise."

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        for msg in history[-10:]:
            role = "user" if msg["sender"] == "user" else "assistant"
            content = msg["content"][:2000] if len(msg["content"]) > 2000 else msg["content"]
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": prompt[:3000]})

    try:
        response = requests.post(
            f"{Config.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": model_name,
                "messages": messages,
                "stream": False,
                "options": {"temperature": 0.7, "num_predict": 8192}
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return {
            "success": True,
            "response": data['message']['content'],
            "model": f"ollama/{model_name}",
            "confidence": 0.8,
            "tokens_used": 0
        }
    except Exception as e:
        logger.error(f"Ollama error: {e}")
        return {
            "success": False,
            "error": str(e),
            "response": "I'm having trouble with the local AI. Please check if Ollama is running.",
            "confidence": 0
        }

def get_document_context(content: str, chat_id: str) -> str:
    if not doc_manager:
        logger.warning("doc_manager not available")
        return ""
    keywords = ["document", "file", "summary", "summarize", "analyze", "content", "read"]
    if not any(k in content.lower() for k in keywords):
        logger.debug(f"No document keywords in message: {content[:50]}...")
        return ""
    
    logger.info(f"Document keywords detected, checking for recent document in chat {chat_id}")
    recent_doc = doc_manager.get_recent_document_by_chat(chat_id)
    if not recent_doc:
        logger.warning(f"No recent document found for chat {chat_id}")
        return ""
    
    logger.info(f"Found document: {recent_doc.filename}, content length: {len(recent_doc.content)}")
    preview = recent_doc.content[:2000]
    if len(recent_doc.content) > 2000:
        preview += "..."
    return f"\n\nThe user has a document titled '{recent_doc.filename}'. Here is its content:\n\n{preview}"

def extract_tool_calls(response: str) -> List[dict]:
    tools = []
    pattern = r'\[TOOL:(\w+)\](.*?)\[/TOOL\]'
    matches = re.findall(pattern, response, re.DOTALL)
    for tool_name, tool_content in matches:
        tools.append({
            "tool": tool_name,
            "input": tool_content.strip()[:1000],
            "timestamp": datetime.now().isoformat()
        })
    return tools

def handle_slash_command(content: str, chat_id: str, user: dict):
    parts = content.split()
    command = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    commands = {
        "/help": cmd_help,
        "/clear": cmd_clear,
        "/export": cmd_export,
        "/focus": cmd_focus,
        "/status": cmd_status,
        "/lock": cmd_lock,
        "/memory": cmd_memory,
        "/model": cmd_model,
        "/persona": cmd_persona,
        "/voice": cmd_voice,
        "/volume": cmd_volume,
        "/brightness": cmd_brightness,
        "/theme": cmd_theme,
        "/systeminfo": cmd_systeminfo,
        "/shutdown": cmd_shutdown,
        "/restart": cmd_restart,
        "/open": cmd_open,
        "/remember": cmd_remember,
    }

    handler = commands.get(command)
    if handler:
        return handler(args, chat_id, user)
    else:
        return jsonify({
            "success": True,
            "message": {"id": str(uuid.uuid4()), "content": content, "sender": "user"},
            "ai_response": {
                "response": f"Unknown command: `{command}`. Type `/help` for available commands.",
                "model": "system"
            }
        })

def cmd_clear(args, chat_id, user):
    try:
        with get_db() as db:
            db.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            db.commit()
        log_activity("chat_cleared", user["id"], {"chat_id": chat_id})
        return jsonify({
            "success": True,
            "message": {"id": str(uuid.uuid4()), "content": "/clear", "sender": "user"},
            "ai_response": {"response": "Conversation cleared.", "model": "system"}
        })
    except Exception as e:
        logger.error(f"Clear chat error: {e}")
        return jsonify({"success": False, "error": "Failed to clear chat"}), 500

def cmd_shutdown(args, chat_id, user):
    try:
        system = platform.system()
        if system == "Windows":
            os.system("shutdown /s /t 5")
        elif system == "Linux":
            os.system("shutdown -h now")
        elif system == "Darwin":
            os.system("sudo shutdown -h now")
        return jsonify({
            "success": True,
            "ai_response": {"response": "Shutting down in 5 seconds...", "model": "system"}
        })
    except Exception as e:
        logger.error(f"Shutdown error: {e}")
        return jsonify({"success": False, "error": "Shutdown failed"}), 500

def cmd_restart(args, chat_id, user):
    try:
        system = platform.system()
        if system == "Windows":
            os.system("shutdown /r /t 5")
        elif system == "Linux":
            os.system("shutdown -r now")
        elif system == "Darwin":
            os.system("sudo shutdown -r now")
        return jsonify({
            "success": True,
            "ai_response": {"response": "Restarting in 5 seconds...", "model": "system"}
        })
    except Exception as e:
        logger.error(f"Restart error: {e}")
        return jsonify({"success": False, "error": "Restart failed"}), 500

def cmd_open(args, chat_id, user):
    if not args:
        return jsonify({
            "success": True,
            "ai_response": {"response": "Usage: /open <app_name> (e.g., /open notepad)", "model": "system"}
        })
    app_name = " ".join(args)
    try:
        if platform.system() == "Windows":
            os.system(f"start {app_name}")
        elif platform.system() == "Darwin":
            os.system(f"open {app_name}")
        else:
            os.system(f"xdg-open {app_name}")
        return jsonify({
            "success": True,
            "ai_response": {"response": f"Opening {app_name}...", "model": "system"}
        })
    except Exception as e:
        logger.error(f"Open error: {e}")
        return jsonify({"success": False, "error": "Failed to open"}), 500

def cmd_export(args, chat_id, user):
    format_type = args[0] if args else "json"
    if format_type not in ["json", "markdown"]:
        format_type = "json"
    return jsonify({
        "success": True,
        "message": {"id": str(uuid.uuid4()), "content": "/export", "sender": "user"},
        "ai_response": {
            "response": f"Export initiated. Use the export button in the chat header to download as {format_type}.",
            "model": "system",
            "action": "export",
            "format": format_type
        }
    })

def cmd_remember(args, chat_id, user):
    if not args:
        return jsonify({
            "success": True,
            "ai_response": {"response": "Usage: /remember [category] fact", "model": "system"}
        })
    fact_text = " ".join(args)
    known_categories = ['identity', 'like', 'dislike', 'work', 'project', 'location', 'birthday', 'age', 'relationship']
    category = 'general'
    if args[0].lower() in known_categories:
        category = args[0].lower()
        fact_text = " ".join(args[1:])
    if not fact_text:
        return jsonify({"success": True, "ai_response": {"response": "Nothing to remember.", "model": "system"}})
    try:
        fact_id = iris_memory.learn_fact('user', fact_text, category, 1.0, is_auto=False, persistent=True, tags=[category])
        log_activity("fact_added", user["id"], {"fact_id": fact_id, "category": category})
        return jsonify({
            "success": True,
            "ai_response": {"response": f"Remembered: {fact_text}", "model": "system"}
        })
    except Exception as e:
        logger.error(f"Remember error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def cmd_focus(args, chat_id, user):
    new_focus = not user.get("focus_mode", False)
    try:
        with get_db() as db:
            db.execute("UPDATE users SET focus_mode = ? WHERE id = ?", (int(new_focus), user["id"]))
            db.commit()
        log_activity("focus_mode_toggled", user["id"], {"enabled": new_focus})
        return jsonify({
            "success": True,
            "focus_mode": new_focus,
            "ai_response": {
                "response": f"{'Enabled' if new_focus else 'Disabled'} Focus mode.",
                "model": "system"
            }
        })
    except Exception as e:
        logger.error(f"Focus mode error: {e}")
        return jsonify({"success": False, "error": "Failed to toggle focus mode"}), 500

def cmd_status(args, chat_id, user):
    stats = get_system_stats()
    return jsonify({
        "success": True,
        "ai_response": {
            "response": f"**System Status**\n\n• CPU: {stats.get('cpu', '--')}%\n• RAM: {stats.get('ram', '--')}%\n• Disk: {stats.get('disk', '--')}%\n• Uptime: {stats.get('uptime', '--')}\n• AI Service: {'Online' if GROQ_AVAILABLE else 'Offline'}",
            "model": "system"
        }
    })

def cmd_lock(args, chat_id, user):
    threading.Thread(target=lock_system).start()
    return jsonify({
        "success": True,
        "ai_response": {"response": "Locking system...", "model": "system"}
    })

def cmd_memory(args, chat_id, user):
    if iris_memory:
        try:
            stats = iris_memory.get_stats()
            return jsonify({
                "success": True,
                "ai_response": {
                    "response": f"**Memory Stats**\n\n• Memories: {stats.get('memories', 0)}\n• Facts: {stats.get('facts', 0)}\n• Categories: {stats.get('categories', 0)}",
                    "model": "system"
                }
            })
        except:
            pass
    return jsonify({
        "success": True,
        "ai_response": {"response": "Memory system is currently unavailable.", "model": "system"}
    })

def cmd_model(args, chat_id, user):
    if args:
        model = args[0].lower()
        if model in Config.MODELS:
            try:
                with get_db() as db:
                    db.execute("UPDATE users SET model = ? WHERE id = ?", (model, user["id"]))
                    db.commit()
                model_info = Config.MODELS[model]
                return jsonify({
                    "success": True,
                    "ai_response": {
                        "response": f"Model changed to **{model}** ({model_info['description']}).",
                        "model": "system"
                    }
                })
            except Exception as e:
                logger.error(f"Model change error: {e}")
    available = ", ".join([f"`{k}`" for k in Config.MODELS.keys()])
    return jsonify({
        "success": True,
        "ai_response": {
            "response": f"**Available Models:** {available}\n\nCurrent: `{user.get('model', 'balanced')}`",
            "model": "system"
        }
    })

def cmd_persona(args, chat_id, user):
    if args:
        persona = args[0].lower()
        if persona in Config.PERSONALITIES:
            try:
                with get_db() as db:
                    db.execute("UPDATE users SET personality = ? WHERE id = ?", (persona, user["id"]))
                    db.commit()
                persona_info = Config.PERSONALITIES[persona]
                return jsonify({
                    "success": True,
                    "ai_response": {
                        "response": f"Personality changed to **{persona_info['name']}**",
                        "model": "system"
                    }
                })
            except Exception as e:
                logger.error(f"Personality change error: {e}")
    available = ", ".join([f"`{k}`" for k in Config.PERSONALITIES.keys()])
    return jsonify({
        "success": True,
        "ai_response": {
            "response": f"**Available Personalities:** {available}\n\nCurrent: `{user.get('personality', 'default')}`",
            "model": "system"
        }
    })

def cmd_voice(args, chat_id, user):
    new_state = not user.get("voice_enabled", False)
    try:
        with get_db() as db:
            db.execute("UPDATE users SET voice_enabled = ? WHERE id = ?", (int(new_state), user["id"]))
            db.commit()
        return jsonify({
            "success": True,
            "ai_response": {
                "response": f"{'Enabled' if new_state else 'Disabled'} voice output.",
                "model": "system"
            }
        })
    except Exception as e:
        logger.error(f"Voice toggle error: {e}")
        return jsonify({"success": False, "error": "Failed to toggle voice"}), 500

def cmd_help(args, chat_id, user):
    commands_list = "\n".join([f"`{cmd}`: {info['desc']} ({info['category']})" 
                                for cmd, info in sorted(Config.COMMANDS.items())])
    return jsonify({
        "success": True,
        "message": {"id": str(uuid.uuid4()), "content": "/help", "sender": "user"},
        "ai_response": {
            "response": f"**Available Commands:**\n\n{commands_list}\n\n**Keyboard Shortcuts:**\n• Ctrl+K - Command palette\n• Ctrl+N - New chat\n• Ctrl+, - Settings\n• Esc - Close panels",
            "model": "system"
        }
    })

def cmd_volume(args, chat_id, user):
    if not args:
        return jsonify({
            "success": True,
            "ai_response": {
                "response": "**Volume Control**\n\nUsage: `/volume up`, `/volume down`, `/volume 50` (set to 50%)",
                "model": "system"
            }
        })
    action = args[0].lower()
    return jsonify({
        "success": True,
        "ai_response": {
            "response": f"Volume command received: `{action}`. (Integration not yet implemented)",
            "model": "system"
        }
    })

def cmd_brightness(args, chat_id, user):
    if not args:
        return jsonify({
            "success": True,
            "ai_response": {
                "response": "**Brightness Control**\n\nUsage: `/brightness up`, `/brightness down`, `/brightness 50` (set to 50%)",
                "model": "system"
            }
        })
    action = args[0].lower()
    return jsonify({
        "success": True,
        "ai_response": {
            "response": f"Brightness command received: `{action}`. (Integration not yet implemented)",
            "model": "system"
        }
    })

def cmd_theme(args, chat_id, user):
    if not args:
        themes_list = ", ".join([f"`{k}`" for k in Config.THEMES.keys()])
        return jsonify({
            "success": True,
            "ai_response": {
                "response": f"**Available Themes:** {themes_list}\n\nCurrent: `{user.get('theme', 'midnight')}`",
                "model": "system"
            }
        })
    theme = args[0].lower()
    if theme in Config.THEMES:
        with get_db() as db:
            db.execute("UPDATE users SET theme = ? WHERE id = ?", (theme, user["id"]))
            db.commit()
        return jsonify({
            "success": True,
            "ai_response": {
                "response": f"Theme changed to **{Config.THEMES[theme]['name']}**",
                "model": "system",
                "action": "theme_changed",
                "theme": theme
            }
        })
    else:
        return jsonify({
            "success": True,
            "ai_response": {
                "response": f"Theme `{theme}` not found. Use `/theme` to see available themes.",
                "model": "system"
            }
        })

def cmd_systeminfo(args, chat_id, user):
    stats = get_system_stats()
    system = platform.system()
    release = platform.release()
    processor = platform.processor()
    python_version = platform.python_version()
    response = f"""**System Information** 

• **OS:** {system} {release}
• **Processor:** {processor}
• **Python:** {python_version}
• **CPU Usage:** {stats.get('cpu', '--')}%
• **RAM Usage:** {stats.get('ram', '--')}%
• **Uptime:** {stats.get('uptime', '--')}
• **AI Service:** {'Online' if GROQ_AVAILABLE else 'Offline'}"""
    return jsonify({
        "success": True,
        "ai_response": {"response": response, "model": "system"}
    })

# ============================================
# API - Voice
# ============================================

@app.route("/api/voice/listen", methods=["POST"])
def voice_listen():
    if not iris_voice or not iris_voice.is_mic_available():
        return jsonify({"success": False, "error": "Microphone not available", "mic_available": False})
    try:
        text = iris_voice.listen(timeout=5, phrase_time_limit=10)
        if text:
            text = text[:500]
            tone = detect_emotional_tone(text)
            return jsonify({"success": True, "text": text, "mic_available": True, "detected_tone": tone})
        else:
            return jsonify({"success": False, "error": "No speech detected", "mic_available": True})
    except Exception as e:
        logger.error(f"Voice listen error: {e}")
        return jsonify({"success": False, "error": "Speech recognition failed", "mic_available": True})

@app.route("/api/voice/speak", methods=["POST"])
def voice_speak():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    text = str(data.get("text", ""))[:500]
    if not text:
        return jsonify({"success": False, "error": "No text provided"}), 400
    profile = data.get("profile", "jarvis")
    if profile not in Config.VOICE_PROFILES:
        profile = "jarvis"
    mood = data.get("mood", "neutral")
    if mood not in ["neutral", "stressed", "confused", "excited", "focused"]:
        mood = "neutral"
    if iris_voice:
        try:
            iris_voice.speak(text, profile, mood)
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Voice speak error: {e}")
            return jsonify({"success": False, "error": "Speech synthesis failed"}), 500
    return jsonify({"success": False, "error": "Voice system not available"}), 503

@app.route("/api/voice/stop", methods=["POST"])
def voice_stop():
    if iris_voice:
        try:
            iris_voice.stop_speaking()
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Voice stop error: {e}")
    return jsonify({"success": False, "error": "Voice system not available"}), 503

@app.route("/api/voice/profiles", methods=["GET"])
def voice_profiles():
    return jsonify({
        "success": True, 
        "profiles": Config.VOICE_PROFILES, 
        "current": iris_voice.profile if iris_voice else "jarvis"
    })

@app.route('/api/models', methods=['GET'])
def list_models():
    """Return list of available and downloaded models."""
    models = model_manager.list_available()
    return jsonify(models)

@app.route('/api/models/download', methods=['POST'])
def download_model():
    """Start downloading a model."""
    data = request.get_json()
    repo_id = data.get('repo_id')
    if not repo_id:
        return jsonify({"error": "repo_id required"}), 400
    model_manager.download_model(repo_id)
    return jsonify({"message": f"Download started for {repo_id}"}), 202

@app.route('/api/models/switch', methods=['POST'])
def switch_model():
    """Load a different model (must be downloaded)."""
    data = request.get_json()
    repo_id = data.get('repo_id')
    if not repo_id:
        return jsonify({"error": "repo_id required"}), 400
    try:
        if model_manager.current_model is not None:
            model_manager.unload_model()
        model_manager.load_model(repo_id)
        return jsonify({"message": f"Switched to {repo_id}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/models/current', methods=['GET'])
def current_model():
    """Get currently loaded model info."""
    return jsonify({
        "active_model": model_manager.current_model_id,
        "device": str(model_manager.device)
    })

@app.route('/api/models/<path:repo_id>', methods=['DELETE'])
def delete_model(repo_id):
    """Delete a downloaded model."""
    success = model_manager.delete_model(repo_id)
    if success:
        return jsonify({"message": f"Deleted {repo_id}"})
    else:
        return jsonify({"error": "Model not found"}), 404

# ============================================
# API - Charts & Data Visualization
# ============================================

@app.route("/api/charts", methods=["POST"])
def create_chart():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    if not MATPLOTLIB_AVAILABLE:
        return jsonify({"success": False, "error": "Matplotlib not available"}), 503

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    chart_type = data.get("type", "line")
    if chart_type not in ["line", "bar", "pie", "scatter"]:
        return jsonify({"success": False, "error": "Invalid chart type"}), 400

    chart_data = data.get("data", {})
    title = str(data.get("title", "Chart"))[:100]
    chat_id = data.get("chat_id")

    if chat_id and not validate_uuid(chat_id):
        return jsonify({"success": False, "error": "Invalid chat ID"}), 400

    try:
        chart_id = str(uuid.uuid4())

        plt.figure(figsize=(10, 6), dpi=100)
        plt.style.use('dark_background')

        if chart_type == "line":
            x = chart_data.get("x", [])
            y = chart_data.get("y", [])
            if len(x) > 1000 or len(y) > 1000:
                return jsonify({"success": False, "error": "Too many data points (max 1000)"}), 400
            plt.plot(x, y, marker='o', linewidth=2, markersize=8)
        elif chart_type == "bar":
            labels = chart_data.get("labels", [])[:50]
            values = chart_data.get("values", [])[:50]
            plt.bar(labels, values, color='#6366f1')
        elif chart_type == "pie":
            labels = chart_data.get("labels", [])[:20]
            values = chart_data.get("values", [])[:20]
            plt.pie(values, labels=labels, autopct='%1.1f%%')
        elif chart_type == "scatter":
            x = chart_data.get("x", [])[:1000]
            y = chart_data.get("y", [])[:1000]
            plt.scatter(x, y, alpha=0.6, s=100)

        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.xlabel(str(chart_data.get("xlabel", ""))[:50], fontsize=12)
        plt.ylabel(str(chart_data.get("ylabel", ""))[:50], fontsize=12)
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        filename = f"chart_{chart_id}.png"
        filepath = os.path.join("charts", filename)
        plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
        plt.close()

        with get_db() as db:
            db.execute("""
                INSERT INTO charts (id, user_id, chat_id, title, chart_type, data, config)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (chart_id, user_id, chat_id, title, chart_type, 
                  json.dumps(chart_data), json.dumps({})))
            db.commit()

        log_activity("chart_created", user_id, {"chart_id": chart_id, "type": chart_type})
        return jsonify({
            "success": True,
            "chart": {
                "id": chart_id,
                "url": f"/charts/{filename}",
                "title": title,
                "type": chart_type
            }
        })
    except Exception as e:
        logger.error(f"Chart creation error: {e}")
        return jsonify({"success": False, "error": "Chart generation failed"}), 500

@app.route("/api/charts", methods=["GET"])
def list_charts():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    try:
        with get_db() as db:
            charts = db.execute("""
                SELECT * FROM charts 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """, (user_id,)).fetchall()

            result = [{
                "id": c["id"],
                "title": c["title"],
                "type": c["chart_type"],
                "created_at": c["created_at"],
                "is_pinned": bool(c["is_pinned"])
            } for c in charts]

        return jsonify({"success": True, "charts": result})
    except Exception as e:
        logger.error(f"List charts error: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

@app.route("/charts/<filename>")
def serve_chart(filename):
    if not re.match(r'^chart_[a-f0-9-]+\.png$', filename):
        return jsonify({"success": False, "error": "Invalid filename"}), 400
    return send_from_directory("charts", filename)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

@app.route('/static/sw.js')
def serve_sw():
    response = make_response(send_from_directory('static', 'sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response

@app.route('/sw.js')
def serve_root_sw():
    return serve_sw()  # reuse your existing function

# ============================================
# API - Memory
# ============================================

@app.route("/api/memory", methods=["GET"])
def api_get_memory():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    if iris_memory:
        try:
            stats = iris_memory.get_stats(user_id=user_id)
            summary = iris_memory.get_memory_summary(user_id=user_id)
            recent = iris_memory.get_recent_context(5, user_id=user_id)
            return jsonify({"success": True, "stats": stats, "summary": summary, "recent_context": recent})
        except Exception as e:
            logger.error(f"Memory API error: {e}")
    return jsonify({"success": False, "error": "Memory not available"}), 503

@app.route("/api/memory/search", methods=["POST"])
def api_search_memory():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    query = str(data.get("query", ""))[:200]
    if not query:
        return jsonify({"success": False, "error": "Query required"}), 400
    if iris_memory:
        try:
            memories = iris_memory.search_memories(query, limit=10)
            result = [{
                "id": m.id,
                "user_msg": m.user_msg[:200] if hasattr(m, 'user_msg') else "",
                "iris_response": m.iris_response[:100] if hasattr(m, 'iris_response') else "",
                "timestamp": m.timestamp if hasattr(m, 'timestamp') else "",
                "importance": m.importance if hasattr(m, 'importance') else 0,
                "tags": m.tags if hasattr(m, 'tags') else []
            } for m in memories]
            return jsonify({"success": True, "memories": result})
        except Exception as e:
            logger.error(f"Memory search error: {e}")
    return jsonify({"success": False, "error": "Memory not available"}), 503

@app.route("/api/memory/graph", methods=["GET"])
def api_memory_graph():
    if iris_memory:
        try:
            graph_data = iris_memory.get_memory_graph()
            return jsonify({"success": True, "graph": graph_data})
        except Exception as e:
            logger.error(f"Memory graph error: {e}")
    return jsonify({"success": False, "error": "Memory not available"}), 503

@app.route("/api/memory/facts", methods=["GET"])
def list_facts():
    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    target_user_id, is_creator_view = get_target_user_id()
    if not target_user_id:
        return jsonify({"success": False, "error": "Invalid user"}), 400

    include_shared = not is_creator_view
    if is_creator_view:
        include_shared = request.args.get('include_shared', 'true').lower() == 'true'

    if not iris_memory:
        return jsonify({"success": False, "error": "Memory not available"}), 503

    try:
        facts = iris_memory.get_all_facts(
            limit=100,
            user_id=target_user_id,
            include_shared=include_shared
        )
        return jsonify({"success": True, "facts": [f.to_dict() for f in facts]})
    except Exception as e:
        logger.error(f"List facts error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/memory/facts", methods=["POST"])
def add_fact():
    if not iris_memory:
        return jsonify({"success": False, "error": "Memory not available"}), 503
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    subject = data.get("subject", "user")
    fact = data.get("fact", "").strip()
    category = data.get("category", "general")
    confidence = data.get("confidence", 1.0)
    if not fact:
        return jsonify({"success": False, "error": "Fact cannot be empty"}), 400
    try:
        fact_id = iris_memory.learn_fact(subject, fact, category, confidence, is_auto=False)
        log_activity("fact_added", get_current_user_id(), {"fact_id": fact_id, "subject": subject, "category": category})
        return jsonify({"success": True, "fact_id": fact_id})
    except Exception as e:
        logger.error(f"Add fact error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/memory/facts/<fact_id>", methods=["PUT"])
def update_fact(fact_id):
    if not iris_memory:
        return jsonify({"success": False, "error": "Memory not available"}), 503
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    try:
        success = iris_memory.update_fact(fact_id, data.get("fact"), data.get("confidence"))
        if success:
            log_activity("fact_updated", get_current_user_id(), {"fact_id": fact_id})
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Fact not found"}), 404
    except Exception as e:
        logger.error(f"Update fact error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/memory/facts/<fact_id>", methods=["DELETE"])
def delete_fact(fact_id):
    if not iris_memory:
        return jsonify({"success": False, "error": "Memory not available"}), 503

    current_user_id = get_current_user_id()
    if not current_user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    fact = iris_memory.get_fact(fact_id)
    if not fact:
        return jsonify({"success": False, "error": "Fact not found"}), 404

    if fact.user_id != current_user_id and not is_creator(current_user_id):
        return jsonify({"success": False, "error": "Access denied"}), 403

    success = iris_memory.delete_fact(fact_id)
    if success:
        log_activity("fact_deleted", current_user_id, {"fact_id": fact_id})
        return jsonify({"success": True})
    else:
        return jsonify({"success": False, "error": "Failed to delete fact"}), 500

@app.route("/api/memory/facts/pending", methods=["GET"])
def get_pending_facts():
    if not iris_memory:
        return jsonify({"success": False, "error": "Memory not available"}), 503
    try:
        facts = iris_memory.get_all_facts(limit=100, pending_only=True)
        return jsonify({"success": True, "facts": [f.to_dict() for f in facts]})
    except Exception as e:
        logger.error(f"List pending facts error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/memory/facts/<fact_id>/confirm", methods=["POST"])
def confirm_fact(fact_id):
    if not iris_memory:
        return jsonify({"success": False, "error": "Memory not available"}), 503
    try:
        with get_db() as db:
            db.execute("UPDATE memory_facts SET confirmed = 1 WHERE id = ?", (fact_id,))
            db.commit()
        log_activity("fact_confirmed", get_current_user_id(), {"fact_id": fact_id})
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Confirm fact error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/memory/facts/confirm-all", methods=["POST"])
def confirm_all_pending():
    if not iris_memory:
        return jsonify({"success": False, "error": "Memory not available"}), 503
    try:
        count = iris_memory.confirm_all_pending()
        log_activity("facts_confirm_all", get_current_user_id(), {"count": count})
        return jsonify({"success": True, "count": count})
    except Exception as e:
        logger.error(f"Confirm all error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/memory/facts/export", methods=["GET"])
def export_facts():
    if not iris_memory:
        return jsonify({"success": False, "error": "Memory not available"}), 503
    try:
        facts = iris_memory.export_facts()
        response = make_response(json.dumps(facts, indent=2))
        response.headers["Content-Type"] = "application/json"
        response.headers["Content-Disposition"] = "attachment; filename=iris_facts.json"
        return response
    except Exception as e:
        logger.error(f"Export facts error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/memory/facts/import", methods=["POST"])
def import_facts():
    if not iris_memory:
        return jsonify({"success": False, "error": "Memory not available"}), 503
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "No file selected"}), 400
    if not file.filename.endswith('.json'):
        return jsonify({"success": False, "error": "Only JSON files allowed"}), 400
    try:
        facts_data = json.load(file)
        count = iris_memory.import_facts(facts_data)
        log_activity("facts_imported", get_current_user_id(), {"count": count})
        return jsonify({"success": True, "count": count})
    except Exception as e:
        logger.error(f"Import facts error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/memory/facts/tags", methods=["GET"])
def get_tags():
    if not iris_memory:
        return jsonify({"success": False, "error": "Memory not available"}), 503
    try:
        tags = iris_memory.get_all_tags()
        return jsonify({"success": True, "tags": tags})
    except Exception as e:
        logger.error(f"Get tags error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/memory/facts/search", methods=["POST"])
def search_facts():
    if not iris_memory:
        return jsonify({"success": False, "error": "Memory not available"}), 503
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    query = data.get("query", "")
    category = data.get("category", None)
    tag = data.get("tag", None)
    try:
        facts = iris_memory.get_all_facts(limit=100, search=query, category=category, tag=tag)
        return jsonify({"success": True, "facts": [f.to_dict() for f in facts]})
    except Exception as e:
        logger.error(f"Search facts error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================
# CREATOR ADMIN API
# ============================================

@app.route("/api/admin/users", methods=["GET"])
def admin_list_users():
    if not is_creator():
        return jsonify({"success": False, "error": "Forbidden"}), 403
    try:
        with get_db() as db:
            users = db.execute("""
                SELECT id, username, email, role, created_at, last_login
                FROM users ORDER BY created_at DESC
            """).fetchall()
            result = [dict(u) for u in users]
        return jsonify({"success": True, "users": result})
    except Exception as e:
        logger.error(f"Admin list users error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/users/<user_id>", methods=["DELETE"])
def admin_delete_user(user_id):
    if not is_creator():
        return jsonify({"success": False, "error": "Forbidden"}), 403
    if user_id == get_current_user_id():
        return jsonify({"success": False, "error": "Cannot delete yourself"}), 400
    try:
        with get_db() as db:
            db.execute("DELETE FROM users WHERE id = ?", (user_id,))
            db.commit()
        log_activity("admin_delete_user", get_current_user_id(), {"deleted_user": user_id})
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"Admin delete user error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/admin/impersonate", methods=["POST"])
def admin_impersonate():
    if not is_creator():
        return jsonify({"success": False, "error": "Forbidden"}), 403
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    target_user_id = data.get('user_id')
    if not target_user_id:
        return jsonify({"success": False, "error": "user_id required"}), 400
    session['impersonator_id'] = session.get('user_id')
    session['user_id'] = target_user_id
    log_activity("admin_impersonate", session['impersonator_id'], {"target": target_user_id})
    return jsonify({"success": True, "message": f"Now impersonating user {target_user_id}"})

@app.route("/api/admin/revert", methods=["POST"])
def admin_revert():
    if 'impersonator_id' not in session:
        return jsonify({"success": False, "error": "Not impersonating"}), 400
    session['user_id'] = session['impersonator_id']
    del session['impersonator_id']
    return jsonify({"success": True})

@app.route("/api/admin/users/<user_id>/export", methods=["GET"])
def admin_export_user(user_id):
    if not is_creator():
        return jsonify({"success": False, "error": "Forbidden"}), 403
    data = {
        "user": get_user_by_id(user_id),
        "facts": [],
        "documents": [],
        "chats": []
    }
    if iris_memory:
        facts = iris_memory.get_all_facts(limit=10000, user_id=user_id)
        data["facts"] = [f.to_dict() for f in facts]
    if doc_manager:
        docs = doc_manager.list_documents(limit=10000, user_id=user_id)
        data["documents"] = docs
    with get_db() as db:
        chats = db.execute("SELECT * FROM chats WHERE user_id = ?", (user_id,)).fetchall()
        data["chats"] = [dict(c) for c in chats]
    return jsonify({"success": True, "data": data})

@app.route("/api/self_destruct", methods=["POST"])
def self_destruct():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400

    voice_ok = data.get('voice') == 'dummy_voice_match'
    face_ok = data.get('face') == 'dummy_face_match'
    # Inside self_destruct()
    password = data.get('password', '')
    user_data = get_user_by_id(user_id)
    if not user_data or not security.verify_password(password, user_data.get('password_hash')):
        log_activity("self_destruct_failed", user_id, {"reason": "invalid password"})
        return jsonify({"success": False, "error": "Authentication failed"}), 403

    if not (voice_ok and face_ok and password_ok):
        log_activity("self_destruct_failed", user_id, {"reason": "factor mismatch"})
        return jsonify({"success": False, "error": "Authentication failed"}), 403

    backup_data = create_backup(user_id)
    send_backup_email(user_id, backup_data)
    wipe_user_data(user_id)

    with get_db() as db:
        db.execute("UPDATE users SET self_destruct_triggered = 1 WHERE id = ?", (user_id,))
        db.commit()

    log_activity("self_destruct_success", user_id)
    return jsonify({"success": True, "message": "Self‑destruct initiated. Backup sent."})

def create_backup(user_id):
    backup = {}
    if iris_memory:
        facts = iris_memory.get_all_facts(limit=10000, user_id=user_id)
        backup['facts'] = [f.to_dict() for f in facts]
    if doc_manager:
        docs = doc_manager.list_documents(limit=10000, user_id=user_id)
        backup['documents'] = docs
    with get_db() as db:
        chats = db.execute("SELECT * FROM chats WHERE user_id = ?", (user_id,)).fetchall()
        backup['chats'] = [dict(c) for c in chats]
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        backup['user'] = dict(user)
    return backup

def send_backup_email(user_id, backup_data):
    import json
    backup_json = json.dumps(backup_data, indent=2)
    filename = f"backup_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join('exports', filename)
    with open(filepath, 'w') as f:
        f.write(backup_json)
    if email_reporter:
        email_reporter.send_report('self_destruct', f"User {user_id} self‑destruct backup", attachments=[Path(filepath)])
    os.remove(filepath)

def wipe_user_data(user_id):
    with get_db() as db:
        db.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM chats WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM documents WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM memory_facts WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM smart_memories WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM concept_links WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM charts WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM automations WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM activity_log WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM game_saves WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM user_states WHERE user_id = ?", (user_id,))
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
    if doc_manager:
        docs = doc_manager.list_documents(limit=10000, user_id=user_id)
        for doc in docs:
            doc_manager.delete_document(doc['id'])

@app.route("/api/creator/schedule_task", methods=["POST"])
def schedule_task():
    if not is_creator():
        return jsonify({"success": False, "error": "Forbidden"}), 403
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    task_type = data.get("task_type")
    execute_at = data.get("execute_at")
    task_data = data.get("data", {})
    if not task_type or not execute_at:
        return jsonify({"success": False, "error": "Missing task_type or execute_at"}), 400

    try:
        exec_time = datetime.fromisoformat(execute_at)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid datetime format"}), 400

    task_id = str(uuid.uuid4())
    with get_db() as db:
        db.execute("""
            INSERT INTO scheduled_tasks (id, user_id, task_type, execute_at, data)
            VALUES (?, ?, ?, ?, ?)
        """, (task_id, get_current_user_id(), task_type, exec_time.isoformat(), json.dumps(task_data)))
        db.commit()

    # Schedule the task with APScheduler
    run_date = exec_time
    scheduler.add_job(
        func=execute_scheduled_task,
        trigger='date',
        run_date=run_date,
        args=[task_id],
        id=task_id,
        replace_existing=True
    )
    log_activity("task_scheduled", get_current_user_id(), {"task_id": task_id, "type": task_type})
    return jsonify({"success": True, "task_id": task_id})

# ============================================
# API - Games
# ============================================

@app.route("/api/games/list", methods=["GET"])
def list_games():
    from skills.maflex_games import list_available_games
    games = list_available_games()
    return jsonify({"success": True, "games": games})

@app.route("/api/games/start/<game_name>", methods=["POST"])
@csrf.exempt
def start_old_game(game_name):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 401
    game = game_manager.start_game(user_id, game_name)
    if not game:
        return jsonify({"success": False, "error": "Game not found"}), 404
    initial_state = game.start()
    return jsonify({
        "success": True,
        "game_id": game.game_id,
        "state": initial_state,
        "full_state": game.get_state(user_id)
    })

@app.route("/api/games/action", methods=["POST"])
@csrf.exempt
def handle_game_action():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 401
    data = request.get_json()
    action = data.get("action")
    args = data.get("args", [])
    game = game_manager.get_game(user_id)
    if not game:
        return jsonify({"success": False, "error": "No active game"}), 400
    result = game.process_action(action, args)
    with get_db() as db:
        game_manager.save_game(user_id, db)
    return jsonify({"success": True, "result": result, "state": game.get_state(user_id)})

@app.route("/api/games/power", methods=["POST"])
@csrf.exempt
def use_power():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 401
    data = request.get_json()
    power = data.get("power")
    args = data.get("args", [])
    game = game_manager.get_game(user_id)
    if not game:
        return jsonify({"success": False, "error": "No active game"}), 400
    result = game.use_power(power, args)
    with get_db() as db:
        game_manager.save_game(user_id, db)
    return jsonify({"success": True, "result": result, "energy": game.energy})

@app.route("/api/games/save", methods=["POST"])
@csrf.exempt
def save_game():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 401
    with get_db() as db:
        success = game_manager.save_game(user_id, db)
    return jsonify({"success": success})

@app.route("/api/games/load", methods=["POST"])
@csrf.exempt
def load_game():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 401
    data = request.get_json() or {}
    game_id = data.get("game_id")
    with get_db() as db:
        game = game_manager.load_game(user_id, db, game_id)
    if not game:
        return jsonify({"success": False, "error": "No saved game found"}), 404
    return jsonify({
        "success": True,
        "game_id": game.game_id,
        "state": game.get_state(user_id)
    })

@app.route("/maflex")
def maflex_universe():
    return app.send_static_file('maflex.html')

@app.route("/maflex.js")
def maflex_js():
    return app.send_static_file('maflex.js')

@app.route("/api/maflex/games", methods=["GET"])
def maflex_list_games():
    if not maflex_manager:
        return jsonify({"success": False, "error": "Maflex not initialized"}), 503
    games = maflex_manager.get_available_games()
    return jsonify({"success": True, "games": games})

@app.route("/api/maflex/start", methods=["POST"])
@csrf.exempt
def maflex_start():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    game_id = data.get("game_id")
    difficulty = data.get("difficulty", "normal")
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "Not authenticated"}), 401
    game = maflex_manager.create_game(user_id, game_id, difficulty)
    if not game:
        return jsonify({"success": False, "error": "Failed to initialize quantum field"}), 500
    difficulty_options = ['easy', 'normal', 'hard']
    game_class = maflex_manager.game_registry.get_game_class(game_id)
    if game_class and hasattr(game_class, 'LEVELS'):
        difficulty_options = list(game_class.LEVELS.keys())
    return jsonify({
        'success': True,
        'game_id': game.game_id,
        'introduction': game.start(),
        'state': game.get_state(),
        'difficulty_options': difficulty_options
    })

@app.route("/api/maflex/action", methods=["POST"])
@csrf.exempt
def maflex_action():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    action = data.get("action")
    args = data.get("args", [])
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    result = maflex_manager.process_action(user_id, action, args)
    return jsonify(result)

@app.route("/api/maflex/power", methods=["POST"])
@csrf.exempt
def maflex_power():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    power_id = data.get("power_id")
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    result = maflex_manager.use_power(user_id, power_id)
    return jsonify(result)

@app.route("/api/maflex/state", methods=["GET"])
def maflex_state():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    game = maflex_manager.get_game(user_id)
    if not game:
        return jsonify({"success": False, "error": "No active game"}), 404
    return jsonify({"success": True, "game": game.get_state()})

@app.route("/api/maflex/end", methods=["POST"])
@csrf.exempt
def maflex_end():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    result = maflex_manager.end_game(user_id)
    return jsonify({"success": result})

@app.route("/api/maflex/saves", methods=["GET"])
def maflex_saves():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        saves = cursor.execute(
            "SELECT id, game_name, difficulty, created_at FROM game_saves WHERE user_id = ? ORDER BY updated_at DESC",
            (user_id,)
        ).fetchall()
        return jsonify({"success": True, "saves": [dict(save) for save in saves]})

@app.route("/api/maflex/load", methods=["POST"])
@csrf.exempt
def maflex_load():
    data = request.get_json()
    save_id = data.get("save_id")
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    with sqlite3.connect(Config.DATABASE) as conn:
        conn.row_factory = sqlite3.Row
        save = conn.execute(
            "SELECT * FROM game_saves WHERE id = ? AND user_id = ?",
            (save_id, user_id)
        ).fetchone()
        if not save:
            return jsonify({"success": False, "error": "Save not found"}), 404
        game_class = maflex_manager.game_registry.get_game_class(save["game_name"].lower().replace(" ", ""))
        if game_class:
            game = game_class(save["id"], user_id, save["difficulty"])
            return jsonify({
                "success": True,
                "game_id": save["id"],
                "state": json.loads(save["state"])
            })
    return jsonify({"success": False, "error": "Failed to load game"}), 500

@app.route("/api/maflex/enter", methods=["POST"])
@csrf.exempt
def enter_maflex():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 401
    maflex_state = {
        "energy": 100,
        "max_energy": 100,
        "active_powers": [],
        "current_game": None,
        "entered_at": datetime.now().isoformat(),
        "achievements": []
    }
    with get_db() as db:
        db.execute("""
            INSERT INTO user_states (user_id, maflex_state, last_updated)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                maflex_state = excluded.maflex_state,
                last_updated = excluded.last_updated
        """, (user_id, json.dumps(maflex_state), datetime.now().isoformat()))
        db.commit()
    log_activity("maflex_entered", user_id, {"energy": 100})
    return jsonify({"success": True, "state": maflex_state, "message": "Welcome to Maflex, traveler. The infinite awaits."})

@app.route("/api/maflex/power/<power_name>", methods=["POST"])
@csrf.exempt
def use_maflex_power(power_name):
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    user = get_current_user()
    if not user:
        return jsonify({"success": False, "error": "User not found"}), 401
    power_costs = {
        'insight': 15,
        'sight': 10,
        'probability': 20,
        'pattern': 25,
        'manifest': 25,
        'adjust': 30,
        'clone': 40,
        'anchor': 50,
        'avatar': 50,
        'dilation': 35,
        'phase': 30,
        'overdrive': 45,
        'whisper': 20,
        'charm': 35,
        'command': 40
    }
    if power_name not in power_costs:
        return jsonify({"success": False, "error": "Unknown power"}), 400
    with get_db() as db:
        row = db.execute(
            "SELECT maflex_state FROM user_states WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if not row:
            return jsonify({"success": False, "error": "Not in Maflex"}), 400
        state = json.loads(row["maflex_state"])
        if state["energy"] < power_costs[power_name]:
            return jsonify({
                "success": False,
                "error": f"Insufficient energy. Need {power_costs[power_name]}, have {state['energy']}"
            }), 400
        state["energy"] -= power_costs[power_name]
        state["active_powers"].append({
            "power": power_name,
            "activated_at": datetime.now().isoformat()
        })
        db.execute(
            "UPDATE user_states SET maflex_state = ? WHERE user_id = ?",
            (json.dumps(state), user_id)
        )
        db.commit()
    effects = {
        "insight": "Temporal Insight activated! Future possibilities become visible.",
        "sight": "Data Sight reveals hidden information and enemy weaknesses.",
        "manifest": "Controlled Manifestation! An item materializes from energy.",
        "avatar": "Avatar Mode engaged! You are now physically present in the game world.",
        "adjust": "World-State Adjustment! Reality parameters are now malleable."
    }
    log_activity("maflex_power_used", user_id, {"power": power_name, "cost": power_costs[power_name]})
    return jsonify({
        "success": True,
        "power": power_name,
        "energy_remaining": state["energy"],
        "effect": effects.get(power_name, "Power activated"),
        "duration": 30
    })

@app.route("/api/maflex/energy", methods=["GET"])
def get_maflex_energy():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    with get_db() as db:
        row = db.execute(
            "SELECT maflex_state FROM user_states WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if not row:
            return jsonify({"success": False, "error": "Not in Maflex"}), 400
        state = json.loads(row["maflex_state"])
        return jsonify({
            "success": True,
            "energy": state["energy"],
            "max_energy": state["max_energy"]
        })

@app.route("/api/maflex/regen", methods=["POST"])
@csrf.exempt
def regen_maflex_energy():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    game = maflex_manager.get_game(user_id)
    if game and game.energy < game.max_energy:
        game.energy = min(game.max_energy, game.energy + 1)
        if hasattr(maflex_manager, '_save_game'):
            maflex_manager._save_game(user_id, game)
    return jsonify({'success': True, 'energy': game.energy if game else 100})

@app.route("/api/maflex/iris", methods=["POST"])
@csrf.exempt
def maflex_iris_chat():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No message provided"}), 400
    message = data.get("message", "")
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        response = loop.run_until_complete(
            maflex_manager.chat_with_iris(user_id, message)
        )
    finally:
        loop.close()
    return jsonify({'success': True, **response})

@app.route("/api/maflex/toggle_ai", methods=["POST"])
@csrf.exempt
def toggle_ai():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    buddy = maflex_manager.get_or_create_ai_buddy(user_id)
    enabled = buddy.toggle()
    return jsonify({'success': True, 'ai_enabled': enabled})

@app.route("/api/maflex/ai_mode", methods=["POST"])
@csrf.exempt
def set_ai_mode():
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    mode = data.get('mode', 'hybrid')
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    buddy = maflex_manager.get_or_create_ai_buddy(user_id)
    success = buddy.set_mode(mode)
    return jsonify({'success': success, 'mode': mode})

# ============================================
# API - System Control
# ============================================

def get_system_stats():
    if not PSUTIL_AVAILABLE:
        return {"status": "disabled"}
    try:
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        return {
            "cpu": psutil.cpu_percent(interval=0.5),
            "ram": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage("/").percent,
            "boot_time": psutil.boot_time(),
            "uptime": str(uptime).split('.')[0],
            "network": {
                "sent": psutil.net_io_counters().bytes_sent,
                "recv": psutil.net_io_counters().bytes_recv
            }
        }
    except Exception as e:
        logger.error(f"System stats error: {e}")
        return {"error": "Failed to get stats"}

def lock_system():
    try:
        system = platform.system()
        if system == "Windows":
            os.system("rundll32.exe user32.dll,LockWorkStation")
        elif system == "Linux":
            os.system("gnome-screensaver-command -l || xscreensaver-command -l || loginctl lock-session")
        elif system == "Darwin":
            os.system("pmset displaysleepnow")
        log_activity("system_locked", get_current_user_id())
        return True
    except Exception as e:
        logger.error(f"Lock system error: {e}")
        return False

@app.route("/api/system/status", methods=["GET"])
def system_status():
    return jsonify({
        "success": True, 
        "stats": get_system_stats(),
        "timestamp": datetime.now().isoformat(),
        "version": "7.0-secure",
        "features": {
            "voice": iris_voice is not None,
            "memory": iris_memory is not None,
            "documents": doc_manager is not None,
            "charts": MATPLOTLIB_AVAILABLE,
            "groq": GROQ_AVAILABLE,
            "csrf": Config.ENABLE_CSRF,
            "rate_limiting": True
        }
    })

@app.route("/api/system/lock", methods=["POST"])
def lock_system_endpoint():
    success = lock_system()
    return jsonify({"success": success})

@app.route("/api/system/screenshot", methods=["POST"])
def take_screenshot():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    if not PYAUTOGUI_AVAILABLE:
        return jsonify({"success": False, "error": "PyAutoGUI not available"}), 503
    try:
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join("data", filename)
        pyautogui.screenshot().save(filepath)
        log_activity("screenshot_taken", user_id, {"filename": filename})
        return jsonify({"success": True, "filename": filename, "url": f"/data/{filename}"})
    except Exception as e:
        logger.error(f"Screenshot error: {e}")
        return jsonify({"success": False, "error": "Screenshot failed"}), 500

@app.route("/data/<filename>")
def serve_data(filename):
    if not re.match(r'^[a-zA-Z0-9_-]+\.(png|jpg|jpeg|gif|json|csv)$', filename):
        return jsonify({"success": False, "error": "Invalid filename"}), 400
    return send_from_directory("data", filename)

# ============================================
# API - Automation
# ============================================

@app.route("/api/automations", methods=["GET"])
def list_automations():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    try:
        with get_db() as db:
            automations = db.execute("""
                SELECT * FROM automations WHERE user_id = ? ORDER BY created_at DESC
            """, (user_id,)).fetchall()
            result = [{
                "id": a["id"],
                "name": a["name"],
                "trigger_type": a["trigger_type"],
                "is_active": bool(a["is_active"]),
                "last_run": a["last_run"]
            } for a in automations]
        return jsonify({"success": True, "automations": result})
    except Exception as e:
        logger.error(f"List automations error: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

@app.route("/api/automations", methods=["POST"])
def create_automation():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    name = str(data.get("name", ""))[:100]
    if not name:
        return jsonify({"success": False, "error": "Name required"}), 400
    trigger_type = str(data.get("trigger_type", ""))[:50]
    if not trigger_type:
        return jsonify({"success": False, "error": "Trigger type required"}), 400
    auto_id = str(uuid.uuid4())
    try:
        with get_db() as db:
            db.execute("""
                INSERT INTO automations (id, user_id, name, trigger_type, trigger_config, actions)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (auto_id, user_id, name, trigger_type,
                  json.dumps(data.get("trigger_config", {})), json.dumps(data.get("actions", []))))
            db.commit()
        log_activity("automation_created", user_id, {"automation_id": auto_id})
        return jsonify({"success": True, "automation_id": auto_id})
    except Exception as e:
        logger.error(f"Create automation error: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

# ============================================
# API - Configuration & Commands
# ============================================

@app.route("/api/config", methods=["GET"])
def get_config():
    return jsonify({
        "success": True,
        "personalities": Config.PERSONALITIES,
        "themes": Config.THEMES,
        "models": {k: v["description"] for k, v in Config.MODELS.items()},
        "reasoning_modes": Config.REASONING_MODES,
        "voice_profiles": Config.VOICE_PROFILES,
        "commands": Config.COMMANDS
    })

@app.route("/api/commands", methods=["GET"])
def get_commands():
    query = request.args.get("q", "")[:50]
    commands = []
    for cmd, info in Config.COMMANDS.items():
        if not query or query.lower() in cmd or query.lower() in info["desc"].lower():
            commands.append({
                "command": cmd,
                "description": info["desc"],
                "category": info["category"]
            })
    return jsonify({"success": True, "commands": commands})

# ============================================
# API - Activity Log
# ============================================

@app.route("/api/activity", methods=["GET"])
def get_activity_log():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    limit = request.args.get("limit", 50, type=int)
    if limit < 1 or limit > 500:
        limit = 50
    try:
        with get_db() as db:
            activities = db.execute("""
                SELECT * FROM activity_log 
                WHERE user_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (user_id, limit)).fetchall()
            result = [{
                "id": a["id"],
                "action": a["action"],
                "details": json.loads(a["details"]) if a["details"] else None,
                "ip_address": a["ip_address"],
                "timestamp": a["timestamp"]
            } for a in activities]
        return jsonify({"success": True, "activities": result})
    except Exception as e:
        logger.error(f"Activity log error: {e}")
        return jsonify({"success": False, "error": "Database error"}), 500

# ============================================
# Error Handlers
# ============================================

@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "Endpoint not found"}), 404
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    if request.path.startswith('/api/'):
        return jsonify({"success": False, "error": "Internal server error"}), 500
    return render_template('500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    logger.warning(f"Rate limit exceeded for {request.remote_addr}")
    return jsonify({
        "success": False, 
        "error": "Rate limit exceeded. Please slow down.",
        "retry_after": e.description
    }), 429

@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    return jsonify({
        "success": False, 
        "error": f"File too large. Maximum size is {Config.MAX_UPLOAD_SIZE // 1024 // 1024}MB"
    }), 413

model_manager = LocalModelManager(models_dir="models")

# ============================================
# Skill Initialization
# ============================================

def init_skills():
    global iris_voice, doc_manager, iris_memory, chart_manager, automation_engine, PILLOW_AVAILABLE
    logger.info("Loading IRIS v7.0 Secure skills...")
    
    # Initialize Smart Memory
    try:
        from skills.smart_memory import SmartMemory
        iris_memory = SmartMemory(Config.DATABASE)
        logger.info("✅ Smart Memory loaded")
    except Exception as e:
        import traceback
        logger.error(f"❌ Smart Memory failed to load:\n{traceback.format_exc()}")
        iris_memory = None
    
    # Initialize Pillow for image validation
    try:
        from PIL import Image
        PILLOW_AVAILABLE = True
        logger.info("✅ Pillow loaded (avatar validation enabled)")
    except ImportError:
        PILLOW_AVAILABLE = False
        logger.warning("⚠️ Pillow not available (avatar upload validation disabled)")
    
    # Initialize NEW Documentation System with AI capabilities
    try:
        from skills.documentation import DocumentationManager, register_documentation_routes
        doc_manager = DocumentationManager(
            db_path=Config.DATABASE.replace('.db', '_docs.db'),  # Separate docs database
            docs_dir="docs"
        )
        # Register all the new API routes
        register_documentation_routes(app, doc_manager)
        logger.info("✅ Documentation System v7.0 with AI capabilities loaded")
        logger.info("   Features: OCR, Summarization, Q&A, Translation, Comparison, NER")
    except Exception as e:
        import traceback
        logger.error(f"❌ Documentation system failed to load:\n{traceback.format_exc()}")
        doc_manager = None
    
    # Initialize Voice System
    try:
        from skills.voice_system import IRISVoiceSystem
        iris_voice = IRISVoiceSystem()
        logger.info("✅ Voice System loaded")
    except Exception as e:
        logger.warning(f"⚠️ Voice not available: {e}")
        iris_voice = None
    
    # Initialize Chart Manager
    try:
        from skills.chart_manager import ChartManager
        chart_manager = ChartManager()
        logger.info("✅ Chart Manager loaded")
    except Exception as e:
        logger.warning(f"⚠️ Chart Manager not available: {e}")
        chart_manager = None
    
    logger.info("🚀 All skills initialization complete!")

init_skills()

# ============================================
# Email Reporter and Scheduler
# ============================================

email_reporter = None
scheduler = None

def init_email_reporter():
    global email_reporter, scheduler
    try:
        email_reporter = EmailReporter(
            db_path=Config.DATABASE,
            doc_manager=doc_manager,
            memory=iris_memory,
            exports_dir="exports"
        )
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=email_reporter.send_daily_report, trigger='cron', hour=8, minute=0, id='daily_report', replace_existing=True)
        scheduler.add_job(func=email_reporter.send_weekly_report, trigger='cron', day_of_week='mon', hour=9, minute=0, id='weekly_report', replace_existing=True)
        scheduler.add_job(func=email_reporter.send_monthly_report, trigger='cron', day=1, hour=10, minute=0, id='monthly_report', replace_existing=True)
        scheduler.start()
        load_scheduled_tasks()
        logger.info("Email reporter and scheduler initialized")
    except Exception as e:
        logger.error(f"Failed to initialize email reporter: {e}")

def load_scheduled_tasks():
    with app.app_context():
        with get_db() as db:
            tasks = db.execute("SELECT * FROM scheduled_tasks WHERE executed = 0 AND execute_at > ?", 
                               (datetime.now().isoformat(),)).fetchall()
            for task in tasks:
                run_date = datetime.fromisoformat(task['execute_at'])
                scheduler.add_job(
                    func=execute_scheduled_task,
                    trigger='date',
                    run_date=run_date,
                    args=[task['id']],
                    id=task['id'],
                    replace_existing=True
                )

# ============================================
# Report Generators for Email Commands
# ============================================

def generate_system_health_report(format='txt'):
    """Generate system health report."""
    stats = get_system_stats()
    content = f"""SYSTEM HEALTH REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CPU Usage: {stats.get('cpu', 'N/A')}%
RAM Usage: {stats.get('ram', 'N/A')}%
Disk Usage: {stats.get('disk', 'N/A')}%
Uptime: {stats.get('uptime', 'N/A')}
"""
    return content, 'system_health.txt', 'text/plain'

def generate_error_logs_report(limit=50, format='txt'):
    """Extract recent error logs."""
    log_file = 'logs/iris.log'
    if not os.path.exists(log_file):
        return "No log file found.", 'error_logs.txt', 'text/plain'
    try:
        with open(log_file, 'r') as f:
            lines = f.readlines()
        errors = [line for line in lines if 'ERROR' in line][-limit:]
        content = f"ERROR LOGS (last {len(errors)} entries)\nGenerated: {datetime.now().isoformat()}\n\n"
        content += "\n".join(errors) if errors else "No errors found."
        return content, 'error_logs.txt', 'text/plain'
    except Exception as e:
        return f"Error reading logs: {e}", 'error_logs.txt', 'text/plain'

def generate_performance_metrics_report(format='txt'):
    """Memory and performance stats."""
    if iris_memory:
        stats = iris_memory.get_stats()
        content = f"""PERFORMANCE METRICS
Generated: {datetime.now().isoformat()}

Memories: {stats.get('memories', 0)}
Facts: {stats.get('facts', 0)}
Concept Links: {stats.get('concept_links', 0)}
Avg Importance: {stats.get('avg_importance', 0)}
Avg Confidence: {stats.get('avg_confidence', 0)}
"""
    else:
        content = "Memory system not available."
    return content, 'performance_metrics.txt', 'text/plain'

def generate_trading_activity_report(format='txt'):
    """Placeholder for trading data – replace with your actual data source."""
    content = f"""TRADING ACTIVITY REPORT
Generated: {datetime.now().isoformat()}

No trading data source configured.
"""
    return content, 'trading_activity.txt', 'text/plain'

def generate_portfolio_snapshot(format='txt'):
    """Placeholder for portfolio snapshot."""
    content = f"""PORTFOLIO SNAPSHOT
Generated: {datetime.now().isoformat()}

Feature under construction.
"""
    return content, 'portfolio_snapshot.txt', 'text/plain'

def generate_security_activity_log(limit=50, format='txt'):
    """Recent security/activity logs."""
    user_id = get_current_user_id()
    with get_db() as db:
        logs = db.execute("""
            SELECT timestamp, action, details FROM activity_log
            WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?
        """, (user_id, limit)).fetchall()
    if not logs:
        return "No recent activity.", 'security_log.txt', 'text/plain'
    content = f"SECURITY ACTIVITY LOG (last {len(logs)} entries)\nGenerated: {datetime.now().isoformat()}\n\n"
    for log in logs:
        content += f"{log['timestamp']} – {log['action']} – {log.get('details','')}\n"
    return content, 'security_log.txt', 'text/plain'

def generate_database_backup(format='txt'):
    """Create a backup of the main database and return the file path."""
    backup_dir = Path('exports')
    backup_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"db_backup_{timestamp}.db"
    backup_path = backup_dir / backup_filename
    shutil.copy2(Config.DATABASE, backup_path)
    return backup_path, backup_filename, 'application/octet-stream'

def generate_api_usage_report(format='txt'):
    """API usage statistics from activity_log."""
    with get_db() as db:
        since = (datetime.now() - timedelta(days=1)).isoformat()
        rows = db.execute("""
            SELECT action, COUNT(*) as count FROM activity_log
            WHERE timestamp > ? GROUP BY action ORDER BY count DESC
        """, (since,)).fetchall()
    content = f"API USAGE REPORT (last 24h)\nGenerated: {datetime.now().isoformat()}\n\n"
    for row in rows:
        content += f"{row['action']}: {row['count']} calls\n"
    return content, 'api_usage.txt', 'text/plain'

def generate_model_usage_summary(format='txt'):
    """Summary of AI model usage from messages."""
    with get_db() as db:
        rows = db.execute("""
            SELECT model, COUNT(*) as count FROM messages
            WHERE sender = 'iris' GROUP BY model ORDER BY count DESC
        """).fetchall()
    content = f"MODEL USAGE SUMMARY\nGenerated: {datetime.now().isoformat()}\n\n"
    for row in rows:
        content += f"{row['model']}: {row['count']} messages\n"
    return content, 'model_usage.txt', 'text/plain'

def generate_system_update_report(format='txt'):
    import platform
    content = f"""SYSTEM UPDATE REPORT
Generated: {datetime.now().isoformat()}

Python Version: {platform.python_version()}
Latest Updates: Not implemented.
"""
    return content, 'system_update.txt', 'text/plain'

def generate_weekly_intelligence_summary(format='txt'):
    content = f"""WEEKLY INTELLIGENCE SUMMARY
Generated: {datetime.now().isoformat()}

[To be implemented – combine system health, memory growth, activity]
"""
    return content, 'weekly_intelligence.txt', 'text/plain'

def generate_file_changes_log(format='txt'):
    content = f"""FILE CHANGES LOG
Generated: {datetime.now().isoformat()}

No file monitoring implemented yet.
"""
    return content, 'file_changes.txt', 'text/plain'

def generate_autonomous_actions_report(format='txt'):
    with get_db() as db:
        actions = db.execute("""
            SELECT * FROM activity_log WHERE action LIKE 'auto_%'
            ORDER BY timestamp DESC LIMIT 50
        """).fetchall()
    content = f"AUTONOMOUS ACTIONS REPORT (last 50)\nGenerated: {datetime.now().isoformat()}\n\n"
    for act in actions:
        content += f"{act['timestamp']} – {act['action']}\n"
    return content, 'autonomous_actions.txt', 'text/plain'

# Registry of all available reports
REPORT_GENERATORS = {
    'system_health': generate_system_health_report,
    'error_logs': generate_error_logs_report,
    'performance_metrics': generate_performance_metrics_report,
    'trading_activity': generate_trading_activity_report,
    'portfolio_snapshot': generate_portfolio_snapshot,
    'security_log': generate_security_activity_log,
    'database_backup': generate_database_backup,
    'api_usage': generate_api_usage_report,
    'model_usage': generate_model_usage_summary,
    'system_update': generate_system_update_report,
    'weekly_intelligence': generate_weekly_intelligence_summary,
    'file_changes': generate_file_changes_log,
    'autonomous_actions': generate_autonomous_actions_report,
}

def send_report_now(report_type, user_id, format='txt'):
    """Generate a report and send it via email immediately. Returns (success, message, attachment_path?)"""
    generator = REPORT_GENERATORS.get(report_type)
    if not generator:
        return False, f"Unknown report type: {report_type}", None
    try:
        result = generator(format=format)
        if isinstance(result, tuple) and len(result) == 3:
            first, filename, mime = result
            # If first is a Path or an existing file path, treat as attachment
            if isinstance(first, Path) or (isinstance(first, str) and os.path.exists(first)):
                # File attachment
                file_path = first
                body = f"Attached is your requested report: {report_type}"
                subject = f"IRIS Report: {report_type.replace('_',' ').title()}"
                if email_reporter:
                    success = email_reporter.send_report_with_attachment(subject, body, file_path, filename, mime)
                    if success:
                        log_activity("report_sent", user_id, {"report_type": report_type, "file": filename})
                        return True, f"Report sent with attachment: {filename}", file_path
                    else:
                        return False, "Email sending failed.", None
            else:
                # Plain text content
                body = first
                subject = f"IRIS Report: {report_type.replace('_',' ').title()}"
                if email_reporter:
                    success = email_reporter.send_report('user_report', f"{subject}\n\n{body}")
                    if success:
                        log_activity("report_sent", user_id, {"report_type": report_type})
                        return True, "Report sent.", None
                    else:
                        return False, "Email sending failed.", None
        else:
            # Unexpected return format
            return False, "Invalid report format", None
    except Exception as e:
        logger.error(f"Report generation error: {e}")
        return False, f"Error generating report: {e}", None
    return False, "Email reporter not available.", None

def execute_scheduled_report(task_id):
    with app.app_context():
        with get_db() as db:
            task = db.execute("SELECT * FROM scheduled_tasks WHERE id = ?", (task_id,)).fetchone()
            if not task or task['executed']:
                return
            db.execute("UPDATE scheduled_tasks SET executed = 1 WHERE id = ?", (task_id,))
            db.commit()
            task_data = json.loads(task['data'])
            report_type = task_data.get('report_type')
            user_id = task_data.get('user_id')
            format = task_data.get('format', 'txt')
            generator = REPORT_GENERATORS.get(report_type)
            if generator:
                try:
                    result = generator(format=format)
                    if isinstance(result, tuple) and len(result) == 3:
                        first, filename, mime = result
                        if isinstance(first, Path) or (isinstance(first, str) and os.path.exists(first)):
                            # File attachment
                            file_path = first
                            body = f"Attached is your scheduled report: {report_type}"
                            subject = f"Scheduled IRIS Report: {report_type.replace('_',' ').title()}"
                            if email_reporter:
                                success = email_reporter.send_report_with_attachment(subject, body, file_path, filename, mime)
                                if success:
                                    log_activity("scheduled_report_sent", user_id, {"task_id": task_id, "report_type": report_type})
                                else:
                                    logger.error(f"Scheduled report email failed for task {task_id}")
                        else:
                            # Plain text
                            body = first
                            subject = f"Scheduled IRIS Report: {report_type.replace('_',' ').title()}"
                            if email_reporter:
                                success = email_reporter.send_report('scheduled_report', f"{subject}\n\n{body}")
                                if success:
                                    log_activity("scheduled_report_sent", user_id, {"task_id": task_id, "report_type": report_type})
                                else:
                                    logger.error(f"Scheduled report email failed for task {task_id}")
                    else:
                        logger.error(f"Unexpected result format for task {task_id}")
                except Exception as e:
                    logger.error(f"Scheduled report execution error: {e}")

def execute_scheduled_task(task_id):
    with app.app_context():
        with get_db() as db:
            task = db.execute("SELECT * FROM scheduled_tasks WHERE id = ?", (task_id,)).fetchone()
            if not task or task['executed']:
                return
            db.execute("UPDATE scheduled_tasks SET executed = 1 WHERE id = ?", (task_id,))
            db.commit()
            task_data = json.loads(task['data'])
            if task['task_type'] == 'email':
                if email_reporter:
                    email_reporter.send_report('scheduled', f"Scheduled task:\n{task_data.get('body','')}")
            # Add other task types as needed
            log_activity("task_executed", task['user_id'], {"task_id": task_id})

@app.route("/api/reports/list", methods=["GET"])
def list_reports():
    return jsonify({
        "success": True,
        "reports": list(REPORT_GENERATORS.keys())
    })

@app.route("/api/user/send_report", endpoint="user_send_report", methods=["POST"])
def user_send_report():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"success": False, "error": "Not logged in"}), 401
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    report_type = data.get("report_type")
    schedule = data.get("schedule", "now")
    format = data.get("format", "txt")
    custom_message = data.get("message", "")

    if not report_type:
        return jsonify({"success": False, "error": "Missing report_type"}), 400

    if schedule == "now":
        success, msg, attachment = send_report_now(report_type, user_id, format)
        if success:
            response = {"success": True, "message": msg}
            if attachment:
                filename = os.path.basename(attachment)
                response["download_url"] = f"/exports/{filename}"
            return jsonify(response)
        else:
            return jsonify({"success": False, "error": msg}), 500
    else:
        try:
            now = datetime.now()
            if schedule.startswith("in "):
                match = re.match(r"in (\d+) minutes?", schedule)
                if match:
                    minutes = int(match.group(1))
                    exec_time = now + timedelta(minutes=minutes)
                else:
                    return jsonify({"success": False, "error": "Invalid schedule format. Use 'in X minutes' or 'at HH:MM'"}), 400
            elif schedule.startswith("at "):
                time_str = schedule[3:].strip()
                try:
                    hour, minute = map(int, time_str.split(':'))
                    exec_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if exec_time < now:
                        exec_time += timedelta(days=1)
                except:
                    return jsonify({"success": False, "error": "Invalid time format. Use HH:MM (24h)"}), 400
            else:
                return jsonify({"success": False, "error": "Schedule must start with 'in' or 'at'"}), 400

            task_id = str(uuid.uuid4())
            task_data = {
                "report_type": report_type,
                "user_id": user_id,
                "format": format,
                "custom_message": custom_message
            }
            with get_db() as db:
                db.execute("""
                    INSERT INTO scheduled_tasks (id, user_id, task_type, execute_at, data)
                    VALUES (?, ?, ?, ?, ?)
                """, (task_id, user_id, 'report', exec_time.isoformat(), json.dumps(task_data)))
                db.commit()

            scheduler.add_job(
                func=execute_scheduled_report,
                trigger='date',
                run_date=exec_time,
                args=[task_id],
                id=task_id,
                replace_existing=True
            )

            log_activity("report_scheduled", user_id, {"task_id": task_id, "report_type": report_type, "execute_at": exec_time.isoformat()})
            return jsonify({"success": True, "message": f"Report scheduled for {exec_time.strftime('%Y-%m-%d %H:%M')}"})
        except Exception as e:
            logger.error(f"Schedule error: {e}")
            return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/creator/send_email", endpoint="creator_send_email", methods=["POST"])
def creator_send_email():
    if not get_current_user_id():
        return jsonify({"success": False, "error": "Not logged in"}), 401
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    subject = data.get("subject", "IRIS User Message")
    body = data.get("body", "")
    if not body:
        return jsonify({"success": False, "error": "Message body required"}), 400
    if email_reporter:
        success = email_reporter.send_user_message(subject, body)
        if success:
            log_activity("user_email_sent", get_current_user_id(), {"subject": subject})
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Email sending failed"}), 500
    return jsonify({"success": False, "error": "Email reporter not available"}), 503

@app.route("/api/creator/schedule_task", endpoint="creator_schedule_task", methods=["POST"])
def schedule_task():
    if not is_creator():
        return jsonify({"success": False, "error": "Forbidden"}), 403
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data"}), 400
    task_type = data.get("task_type")
    execute_at = data.get("execute_at")
    task_data = data.get("data", {})
    if not task_type or not execute_at:
        return jsonify({"success": False, "error": "Missing task_type or execute_at"}), 400

    try:
        exec_time = datetime.fromisoformat(execute_at)
    except ValueError:
        return jsonify({"success": False, "error": "Invalid datetime format"}), 400

    task_id = str(uuid.uuid4())
    with get_db() as db:
        db.execute("""
            INSERT INTO scheduled_tasks (id, user_id, task_type, execute_at, data)
            VALUES (?, ?, ?, ?, ?)
        """, (task_id, get_current_user_id(), task_type, exec_time.isoformat(), json.dumps(task_data)))
        db.commit()

    scheduler.add_job(
        func=execute_scheduled_task,
        trigger='date',
        run_date=exec_time,
        args=[task_id],
        id=task_id,
        replace_existing=True
    )
    log_activity("task_scheduled", get_current_user_id(), {"task_id": task_id, "type": task_type})
    return jsonify({"success": True, "task_id": task_id})

init_email_reporter()
load_scheduled_tasks()

# ============================================
# Main Entry Point
# ============================================

if __name__ == "__main__":
    print("🎮 MAFLEX GAMES UNIVERSE v3.0 - THE FUTURE EDITION")
    print("=" * 50)
    print("\nAvailable Games:")
    if maflex_manager:
        games = maflex_manager.game_registry.list_games()
        for game in games:
            print(f"  {game['icon']} {game['name']} - {game['category']}")
        print(f"\nTotal: {len(games)} games")
    else:
        print("⚠️  Maflex manager not initialized")
    print("\n✅ System ready")
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║   IRIS Ultimate v7.0 SECURE - THE CONSCIOUS AI WORKSPACE         ║
    ║                                                                  ║
    ║   🔒 Security Features:                                          ║
    ║   • Environment variable configuration (no hardcoded secrets)    ║
    ║   • CSRF protection on all state-changing operations             ║
    ║   • Input validation and sanitization                            ║
    ║   • SQL injection prevention (parameterized queries)             ║
    ║   • XSS protection headers and sanitization                      ║
    ║   • Secure file upload with type validation                        ║
    ║   • Comprehensive audit logging                                  ║
    ║                                                                  ║
    ║   🔑 API Key Configuration:                                      ║
    ║   • PRIMARY:   For balanced/powerful models (llama-3.3-70b)      ║
    ║   • SECONDARY: For fast models (llama-3.1-8b)                    ║
    ║                                                                  ║
    ║   🌐 Access: http://localhost:5000                               ║
    ║   ⌨️  Press Ctrl+K for Command Palette                           ║
    ║                                                                  ║
    ║   ⚡ Press Ctrl+C to stop                                         ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    if not Config.GROQ_API_KEY_PRIMARY:
        print("🔴 WARNING: GROQ_API_KEY_PRIMARY not set! AI features will be unavailable.")
        print("   Set it with: export GROQ_API_KEY_PRIMARY='your-key-here'")
    import atexit
    atexit.register(lambda: scheduler.shutdown() if scheduler else None)
    app.run(
        host=os.environ.get('FLASK_HOST', '0.0.0.0'),
        port=int(os.environ.get('FLASK_PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true',
        threaded=True
    )
