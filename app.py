"""IRIS v9 Main Application — Modular Blueprint Architecture
Jarvis Edition: Vercel-ready, Postgres-backed, Proactive AI
3D Face Support: Mixamo FBX with Three.js
"""
import os
import sys
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, Response, stream_with_context, g, send_from_directory
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix

from config import config
from core.db import db
from modules.consciousness import consciousness
from modules.security import security_manager
from modules.proactive_engine import proactive_engine
from modules.autonomous import autonomous_engine

# Import blueprints
from api.routes.auth import auth_bp
from api.routes.chat import chat_bp
from api.routes.voice import voice_bp
from api.routes.vision import vision_bp
from api.routes.phone import phone_bp
from api.routes.calendar import calendar_bp
from api.routes.notes import notes_bp
from api.routes.math import math_bp
from api.routes.projects import projects_bp
from api.routes.self_improve import self_improve_bp
from api.routes.consciousness import consciousness_bp
from api.routes.memory import memory_bp
from api.routes.autonomous import autonomous_bp
from api.routes.proactive import proactive_bp
from api.routes.mobile import mobile_bp
from api.routes.tools import tools_bp
from api.routes.email import email_bp
from api.routes.news import news_bp
from api.routes.sports import sports_bp
from api.routes.image import image_bp
from api.routes.gateway import gateway_bp
from api.routes.system import system_bp
from api.routes.intelligence import intelligence_bp

# ─── Logging Setup ───
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(config.DATA_DIR, 'iris.log')) if config.LOG_TO_FILE else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# ─── Flask App ───
app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = config.FLASK_SECRET_KEY
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
CORS(app, resources={r"/api/*": {"origins": "*", "supports_credentials": True}})

# ─── Register Blueprints ───
blueprints = [
    auth_bp, chat_bp, voice_bp, vision_bp, phone_bp,
    calendar_bp, notes_bp, math_bp, projects_bp,
    self_improve_bp, consciousness_bp, memory_bp,
    autonomous_bp, proactive_bp, mobile_bp, tools_bp,
    email_bp, news_bp, sports_bp, image_bp,
    gateway_bp, system_bp, intelligence_bp
]

for bp in blueprints:
    app.register_blueprint(bp)
    logger.info(f"Registered blueprint: {bp.name}")

# ─── Request Timing & Logging ───
@app.before_request
def before_request():
    g.start_time = datetime.now()
    logger.info(f"→ {request.method} {request.path} from {request.remote_addr}")

@app.after_request
def after_request(response):
    duration = (datetime.now() - g.start_time).total_seconds() if hasattr(g, 'start_time') else 0
    logger.info(f"← {request.method} {request.path} {response.status_code} ({duration:.3f}s)")
    return response

# ─── Startup ───
logger.info("🚀 IRIS v9 Jarvis Edition starting up...")
autonomous_engine.start()
proactive_engine.start()
logger.info("✅ All engines started")

# ═══════════════════════════════════════════════════════════════
# WEB PAGES
# ═══════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('iris.html')

@app.route('/voice')
def voice_page():
    return render_template('iris_voice.html')

@app.route('/face')
def face_page():
    """Serve 3D face if FBX exists, otherwise fallback to 2D face."""
    fbx_path = os.path.join(app.static_folder, '3d', 'IRIS.fbx')
    if os.path.exists(fbx_path):
        logger.info("🎭 Serving 3D face (Mixamo model found)")
        return render_template('iris_face_3d.html')
    else:
        logger.info("🎨 Serving 2D face (no 3D model found)")
        return render_template('iris_face.html')

@app.route('/face/2d')
def face_2d():
    """Force 2D face."""
    return render_template('iris_face.html')

@app.route('/face/3d')
def face_3d():
    """Force 3D face (shows error if no model)."""
    return render_template('iris_face_3d.html')

# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=config.DEBUG)
else:
    application = app
