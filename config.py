"""IRIS v8 Configuration — Infinite Reactive Intelligence System"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Aevibron Gateway
    AEVIBRON_BASE_URL = os.getenv("AEVIBRON_BASE_URL", "https://aevibron-gateway.vercel.app/api/v1")
    AEVIBRON_API_KEY = os.getenv("AEVIBRON_API_KEY", "")
    AEVIBRON_ACCESS_TOKEN = os.getenv("AEVIBRON_ACCESS_TOKEN", "")

    # GitHub / Vercel
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
    VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
    VERCEL_TEAM_ID = os.getenv("VERCEL_TEAM_ID", "")

    # Security
    IRIS_PASSWORD_HASH = os.getenv("IRIS_PASSWORD_HASH", "")
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "iris-v8-secret-dev-only")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/iris_v8.db")

    # Voice & Audio
    EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "en-US-AriaNeural")
    WAKE_WORD = os.getenv("WAKE_WORD", "hey iris")
    WAKE_WORD_SENSITIVITY = float(os.getenv("WAKE_WORD_SENSITIVITY", "0.7"))

    # Email (Gmail + Resend)
    IRIS_EMAIL_SENDER = os.getenv("IRIS_EMAIL_SENDER", "")
    IRIS_EMAIL_APP_PASSWORD = os.getenv("IRIS_EMAIL_APP_PASSWORD", "")
    IRIS_EMAIL_RECIPIENT = os.getenv("IRIS_EMAIL_RECIPIENT", "")
    IRIS_RESEND_API_KEY = os.getenv("IRIS_RESEND_API_KEY", "")

    # News
    IRIS_FREENEWS_API_KEY = os.getenv("IRIS_FREENEWS_API_KEY", "")

    # Sports
    IRIS_APISPORTS_KEY = os.getenv("IRIS_APISPORTS_KEY", "")
    IRIS_ODDS_API_KEY = os.getenv("IRIS_ODDS_API_KEY", "")

    # Image Processing
    IRIS_REMOVEBG_API_KEY = os.getenv("IRIS_REMOVEBG_API_KEY", "")

    # VoiceRSS TTS
    IRIS_VOICERSS_API_KEY = os.getenv("IRIS_VOICERSS_API_KEY", "")

    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
    LEARNINGS_DIR = os.path.join(DATA_DIR, "iris_learnings")
    KNOWLEDGE_DIR = os.path.join(DATA_DIR, "iris_knowledge")
    SELF_DIR = os.path.join(DATA_DIR, "iris_self")
    VECTOR_DIR = os.path.join(DATA_DIR, "vector_db")
    BACKUPS_DIR = os.path.join(DATA_DIR, "backups")
    SANDBOX_DIR = os.path.join(DATA_DIR, "sandbox")
    CALENDAR_DIR = os.path.join(DATA_DIR, "calendar")
    NOTES_DIR = os.path.join(DATA_DIR, "notes")

    # Agent
    MAX_TOOL_ITERATIONS = 25
    MAX_RECOVERY_ATTEMPTS = 3

    # Aevibron Models
    DEFAULT_MODEL = "Aevibron Core"
    FAST_MODEL = "Aevibron Flash"
    DEEP_MODEL = "Aevibron Prime"
    LIGHTNING_MODEL = "Aevibron Swift"
    VISION_MODEL = "Aevibron Vision"
    SPEECH_MODEL = "Aevibron Speech"
    AUDIO_MODEL = "Aevibron Audio"
    MULTILINGUAL_MODEL = "Aevibron Quantum"
    AGENTIC_MODEL = "Aevibron Compound"
    OSS_MODEL = "Aevibron OSS"

    # Owner
    OWNER_NAME = "Infinite Vybeflix"
    OWNER_ALIAS = "Infinite"

    # Swarm
    SWARM_REDIS_URL = os.getenv("SWARM_REDIS_URL", "redis://localhost:6379/0")
    SWARM_ENABLED = os.getenv("SWARM_ENABLED", "False").lower() == "true"

    # Phone Bridge
    PHONE_BRIDGE_ENABLED = os.getenv("PHONE_BRIDGE_ENABLED", "False").lower() == "true"
    ADB_DEVICE_ID = os.getenv("ADB_DEVICE_ID", "")

config = Config()
