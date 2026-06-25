"""IRIS v7 Configuration Loader"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Aevibron Gateway
    AEVIBRON_BASE_URL = os.getenv("AEVIBRON_BASE_URL", "https://aevibron-gateway.vercel.app/api/v1")
    AEVIBRON_API_KEY = os.getenv("AEVIBRON_API_KEY", "")
    AEVIBRON_ACCESS_TOKEN = os.getenv("AEVIBRON_ACCESS_TOKEN", "")

    # GitHub
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")

    # Vercel
    VERCEL_TOKEN = os.getenv("VERCEL_TOKEN", "")
    VERCEL_TEAM_ID = os.getenv("VERCEL_TEAM_ID", "")

    # Security
    IRIS_PASSWORD_HASH = os.getenv("IRIS_PASSWORD_HASH", "")
    WEBAUTHN_RP_NAME = os.getenv("WEBAUTHN_RP_NAME", "IRIS")
    WEBAUTHN_RP_ID = os.getenv("WEBAUTHN_RP_ID", "localhost")
    WEBAUTHN_ORIGIN = os.getenv("WEBAUTHN_ORIGIN", "http://localhost:5000")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/iris.db")

    # Voice
    EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "en-US-AriaNeural")

    # App
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "iris-secret-dev-only")
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"

    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
    LEARNINGS_DIR = os.path.join(DATA_DIR, "iris_learnings")
    KNOWLEDGE_DIR = os.path.join(DATA_DIR, "iris_knowledge")
    SELF_DIR = os.path.join(DATA_DIR, "iris_self")
    VECTOR_DIR = os.path.join(DATA_DIR, "vector_db")

    # Agent
    MAX_TOOL_ITERATIONS = 25

    # AEVIBRON MODELS - CORRECT NAMES
    DEFAULT_MODEL = "Aevibron Core"           # General reasoning, coding, analysis
    FAST_MODEL = "Aevibron Flash"              # Ultra-fast responses
    DEEP_MODEL = "Aevibron Prime"              # Maximum capability, deep reasoning
    LIGHTNING_MODEL = "Aevibron Swift"         # Lightning-fast, cost-efficient
    VISION_MODEL = "Aevibron Vision"           # Multimodal - images, diagrams
    SPEECH_MODEL = "Aevibron Speech"           # Text-to-speech, audio generation
    AUDIO_MODEL = "Aevibron Audio"             # Speech recognition, transcription
    MULTILINGUAL_MODEL = "Aevibron Quantum"    # Advanced multilingual reasoning
    AGENTIC_MODEL = "Aevibron Compound"        # Agentic tool-use, multi-step
    OSS_MODEL = "Aevibron OSS"                 # Open-source scale, research

    # User
    OWNER_NAME = "Infinite Vybeflix"
    OWNER_ALIAS = "Infinite"

config = Config()
