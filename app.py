"""IRIS v7 - Complete Application with All Phases"""
import os
import json
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import config
from db import db
from security import security_manager
from aevibron_client import aevibron
from orchestrator import orchestrator
from documentation import document_processor
from smart_memory import smart_memory
from chess_engine import chess_engine
from voice_system import voice_system

# Phase 2 imports
from self_improve import self_improvement
from autonomous import autonomous_engine
from consciousness import consciousness
from project_generator import project_generator

# Phase 3 imports
from sandbox_executor import sandbox_executor
from predictive_engine import predictive_engine
from swarm_coordinator import swarm_coordinator
from multimodal_handler import multimodal_handler
from chroma_memory import chroma_memory
from copilot_bridge import copilot_bridge
from mobile_api import mobile_api

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = config.FLASK_SECRET_KEY
CORS(app)

def require_auth(f):
    def decorated(*args, **kwargs):
        session_id = request.headers.get("X-Session-ID") or session.get("session_id")
        if not session_id or not security_manager.validate_session(session_id):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route("/")
def index():
    return render_template("iris.html")

@app.route("/face")
def face():
    return voice_system.get_face_html()

# === AUTH ===
@app.route("/api/auth", methods=["POST"])
def authenticate():
    data = request.get_json()
    password = data.get("password")
    fingerprint = data.get("fingerprint")

    if password and security_manager.verify_password(password):
        session_id = security_manager.create_session()
        session["session_id"] = session_id
        return jsonify({"success": True, "session_id": session_id, "message": "Welcome back, Infinite.", "fingerprint_supported": True})

    if fingerprint and security_manager.verify_device_fingerprint(fingerprint):
        session_id = security_manager.create_session()
        session["session_id"] = session_id
        return jsonify({"success": True, "session_id": session_id, "message": "Welcome back, Infinite.", "auth_method": "fingerprint"})

    return jsonify({"success": False, "error": "Invalid credentials"}), 401

# === CHAT ===
@app.route("/api/chat", methods=["POST"])
@require_auth
def chat():
    data = request.get_json()
    user_input = data.get("message", "")
    session_id = request.headers.get("X-Session-ID") or session.get("session_id")
    consciousness.on_event("user_message", {"message": user_input})

    def generate():
        for update in orchestrator.process(user_input, session_id):
            yield f"data: {json.dumps(update)}

"
        yield "data: [DONE]

"

    return app.response_class(generate(), mimetype="text/event-stream")

@app.route("/api/chat/sync", methods=["POST"])
@require_auth
def chat_sync():
    data = request.get_json()
    user_input = data.get("message", "")
    session_id = request.headers.get("X-Session-ID") or session.get("session_id")
    consciousness.on_event("user_message", {"message": user_input})

    updates = []
    for update in orchestrator.process(user_input, session_id):
        updates.append(update)
        if update.get("final"):
            break

    return jsonify({"updates": updates})

# === DOCUMENTS ===
@app.route("/api/upload", methods=["POST"])
@require_auth
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    temp_path = os.path.join(config.UPLOADS_DIR, secure_filename(file.filename))
    file.save(temp_path)
    result = document_processor.process_upload(temp_path, file.filename)
    return jsonify(result)

@app.route("/api/documents", methods=["GET"])
@require_auth
def list_documents():
    return jsonify(document_processor.get_document_stats())

@app.route("/api/documents/search", methods=["GET"])
@require_auth
def search_documents():
    query = request.args.get("q", "")
    semantic = request.args.get("semantic", "true").lower() == "true"
    return jsonify({"results": document_processor.search_documents(query, semantic=semantic)})

# === CHESS ===
@app.route("/api/chess/new", methods=["POST"])
@require_auth
def chess_new():
    data = request.get_json()
    session_id = request.headers.get("X-Session-ID")
    return jsonify(chess_engine.new_game(session_id, data.get("opponent", "user")))

@app.route("/api/chess/move", methods=["POST"])
@require_auth
def chess_move():
    data = request.get_json()
    session_id = request.headers.get("X-Session-ID")
    return jsonify(chess_engine.make_move(session_id, data.get("move")))

@app.route("/api/chess/stats", methods=["GET"])
@require_auth
def chess_stats():
    return jsonify(chess_engine.get_stats())

# === VOICE ===
@app.route("/api/voice/speak", methods=["POST"])
@require_auth
def voice_speak():
    data = request.get_json()
    text = data.get("text", "")
    emotion = data.get("emotion", "neutral")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(voice_system.speak(text, emotion))
    loop.close()

    if result.get("success"):
        return send_file(result["audio_path"], mimetype="audio/mpeg")
    return jsonify(result), 500

# === MEMORY ===
@app.route("/api/memory", methods=["GET", "POST"])
@require_auth
def memory():
    if request.method == "GET":
        query = request.args.get("q", "")
        return jsonify({"memories": smart_memory.recall(query)})

    data = request.get_json()
    fact = data.get("fact")
    category = data.get("category", "general")
    smart_memory.learn_about_owner(fact, category)
    return jsonify({"success": True})

@app.route("/api/owner", methods=["GET", "PUT"])
@require_auth
def owner_profile():
    if request.method == "GET":
        return jsonify(smart_memory.get_owner_profile())
    data = request.get_json()
    smart_memory.update_owner_profile(**data)
    return jsonify({"success": True})

# === PHASE 2: SELF-IMPROVEMENT ===
@app.route("/api/self/analyze", methods=["GET"])
@require_auth
def self_analyze():
    return jsonify(self_improvement.analyze_self())

@app.route("/api/self/fix", methods=["POST"])
@require_auth
def self_fix():
    result = self_improvement.self_diagnose_and_fix()
    if result.get("success"):
        consciousness.on_event("self_modified", result)
    return jsonify(result)

@app.route("/api/self/codebase", methods=["GET"])
@require_auth
def self_codebase():
    return jsonify(self_improvement.get_own_codebase_map())

@app.route("/api/self/history", methods=["GET"])
@require_auth
def self_history():
    return jsonify({"changes": self_improvement.get_change_history()})

# === PHASE 2: CONSCIOUSNESS ===
@app.route("/api/consciousness/state", methods=["GET"])
@require_auth
def consciousness_state():
    return jsonify(consciousness.get_emotional_state())

@app.route("/api/consciousness/reflect", methods=["GET"])
@require_auth
def consciousness_reflect():
    return jsonify({"reflection": consciousness.reflect()})

@app.route("/api/consciousness/identity", methods=["GET"])
@require_auth
def consciousness_identity():
    return jsonify({"identity": consciousness.get_identity_statement()})

@app.route("/api/consciousness/thoughts", methods=["GET"])
@require_auth
def consciousness_thoughts():
    return jsonify({"thoughts": consciousness.get_recent_thoughts()})

# === PHASE 2: AUTONOMOUS ===
@app.route("/api/autonomous/start", methods=["POST"])
@require_auth
def autonomous_start():
    return jsonify(autonomous_engine.start())

@app.route("/api/autonomous/stop", methods=["POST"])
@require_auth
def autonomous_stop():
    return jsonify(autonomous_engine.stop())

@app.route("/api/autonomous/status", methods=["GET"])
@require_auth
def autonomous_status():
    return jsonify(autonomous_engine.get_status())

@app.route("/api/autonomous/queue", methods=["POST"])
@require_auth
def autonomous_queue():
    data = request.get_json()
    task_id = autonomous_engine.queue_task(
        description=data.get("description"),
        priority=data.get("priority", 5),
        estimated_minutes=data.get("estimated_minutes", 10),
        task_type=data.get("type", "general")
    )
    return jsonify({"success": True, "task_id": task_id})

@app.route("/api/autonomous/schedule", methods=["POST"])
@require_auth
def autonomous_schedule():
    from datetime import datetime
    data = request.get_json()
    run_at = datetime.fromisoformat(data.get("run_at"))
    task_id = autonomous_engine.schedule_task(
        description=data.get("description"),
        run_at=run_at,
        recurring=data.get("recurring", False),
        interval_hours=data.get("interval_hours", 24)
    )
    return jsonify({"success": True, "task_id": task_id})

# === PHASE 2: PROJECT GENERATOR ===
@app.route("/api/project/generate", methods=["POST"])
@require_auth
def project_generate():
    data = request.get_json()
    result = project_generator.generate_project(
        project_name=data.get("name"),
        template=data.get("template", "nextjs"),
        description=data.get("description", "")
    )
    return jsonify(result)

@app.route("/api/project/deploy", methods=["POST"])
@require_auth
def project_deploy():
    data = request.get_json()
    result = project_generator.deploy_project(
        project_name=data.get("name"),
        repo_name=data.get("repo_name"),
        deploy_to_vercel=data.get("vercel", True)
    )
    return jsonify(result)

@app.route("/api/project/list", methods=["GET"])
@require_auth
def project_list():
    return jsonify({"projects": project_generator.get_projects()})

# === PHASE 3: SANDBOX ===
@app.route("/api/sandbox/execute", methods=["POST"])
@require_auth
def sandbox_execute():
    data = request.get_json()
    code = data.get("code", "")
    allowed_modules = data.get("modules", None)
    result = sandbox_executor.execute_python(code, allowed_modules)
    return jsonify(result)

@app.route("/api/sandbox/shell", methods=["POST"])
@require_auth
def sandbox_shell():
    data = request.get_json()
    command = data.get("command", "")
    allowed_commands = data.get("allowed", None)
    result = sandbox_executor.execute_shell(command, allowed_commands)
    return jsonify(result)

# === PHASE 3: PREDICTIVE ===
@app.route("/api/predictive/patterns", methods=["GET"])
@require_auth
def predictive_patterns():
    return jsonify(predictive_engine.analyze_patterns())

@app.route("/api/predictive/next", methods=["GET"])
@require_auth
def predictive_next():
    return jsonify(predictive_engine.predict_next_action())

@app.route("/api/predictive/suggest", methods=["GET"])
@require_auth
def predictive_suggest():
    suggestion = predictive_engine.proactive_suggestion()
    return jsonify({"suggestion": suggestion})

# === PHASE 3: SWARM ===
@app.route("/api/swarm/status", methods=["GET"])
@require_auth
def swarm_status():
    return jsonify(swarm_coordinator.get_status())

@app.route("/api/swarm/assign", methods=["POST"])
@require_auth
def swarm_assign():
    data = request.get_json()
    result = swarm_coordinator.assign_project(data.get("description", ""))
    return jsonify(result)

@app.route("/api/swarm/agent/<agent_id>/results", methods=["GET"])
@require_auth
def swarm_agent_results(agent_id):
    return jsonify({"results": swarm_coordinator.get_agent_results(agent_id)})

# === PHASE 3: MULTIMODAL ===
@app.route("/api/multimodal/image/generate", methods=["POST"])
@require_auth
def multimodal_image_generate():
    data = request.get_json()
    result = multimodal_handler.generate_image(
        prompt=data.get("prompt"),
        size=data.get("size", "1024x1024"),
        style=data.get("style", "vivid")
    )
    return jsonify(result)

@app.route("/api/multimodal/image/analyze", methods=["POST"])
@require_auth
def multimodal_image_analyze():
    data = request.get_json()
    result = multimodal_handler.analyze_image(
        image_path=data.get("path"),
        question=data.get("question", "What is in this image?")
    )
    return jsonify(result)

@app.route("/api/multimodal/media", methods=["GET"])
@require_auth
def multimodal_media():
    return jsonify({"media": multimodal_handler.get_media_library()})

# === PHASE 3: CHROMA MEMORY ===
@app.route("/api/chroma/add", methods=["POST"])
@require_auth
def chroma_add():
    data = request.get_json()
    success = chroma_memory.add_memory(
        text=data.get("text"),
        metadata=data.get("metadata"),
        memory_id=data.get("id")
    )
    return jsonify({"success": success})

@app.route("/api/chroma/search", methods=["GET"])
@require_auth
def chroma_search():
    query = request.args.get("q", "")
    n = int(request.args.get("n", 10))
    results = chroma_memory.search(query, n_results=n)
    return jsonify({"results": results})

@app.route("/api/chroma/stats", methods=["GET"])
@require_auth
def chroma_stats():
    return jsonify(chroma_memory.get_stats())

# === PHASE 3: COPILOT ===
@app.route("/api/copilot/complete", methods=["POST"])
@require_auth
def copilot_complete():
    data = request.get_json()
    result = copilot_bridge.get_inline_completion(
        file_path=data.get("file"),
        line=data.get("line", 1),
        column=data.get("column", 0),
        prefix=data.get("prefix", ""),
        language=data.get("language", "python")
    )
    return jsonify(result)

@app.route("/api/copilot/explain", methods=["POST"])
@require_auth
def copilot_explain():
    data = request.get_json()
    result = copilot_bridge.get_code_explanation(
        file_path=data.get("file"),
        start_line=data.get("start", 1),
        end_line=data.get("end", 1)
    )
    return jsonify(result)

@app.route("/api/copilot/refactor", methods=["POST"])
@require_auth
def copilot_refactor():
    data = request.get_json()
    result = copilot_bridge.get_refactoring_suggestion(
        file_path=data.get("file"),
        start_line=data.get("start", 1),
        end_line=data.get("end", 1)
    )
    return jsonify(result)

@app.route("/api/copilot/bugs", methods=["POST"])
@require_auth
def copilot_bugs():
    data = request.get_json()
    result = copilot_bridge.get_bug_detection(data.get("file"))
    return jsonify(result)

# === PHASE 3: MOBILE ===
@app.route("/api/mobile/dashboard", methods=["GET"])
@require_auth
def mobile_dashboard():
    return jsonify(mobile_api.get_mobile_dashboard())

@app.route("/api/mobile/sync", methods=["POST"])
@require_auth
def mobile_sync():
    data = request.get_json()
    result = mobile_api.sync_offline_data(
        user_id=data.get("user_id", "owner"),
        pending_actions=data.get("actions", [])
    )
    return jsonify(result)

@app.route("/api/mobile/push/register", methods=["POST"])
@require_auth
def mobile_push_register():
    data = request.get_json()
    success = mobile_api.register_push_token(
        user_id=data.get("user_id", "owner"),
        token=data.get("token"),
        platform=data.get("platform", "fcm")
    )
    return jsonify({"success": success})

@app.route("/api/mobile/quick-actions", methods=["GET"])
@require_auth
def mobile_quick_actions():
    return jsonify({"actions": mobile_api.get_quick_actions()})

@app.route("/api/mobile/biometric", methods=["POST"])
@require_auth
def mobile_biometric():
    data = request.get_json()
    result = mobile_api.handle_biometric_auth(
        user_id=data.get("user_id", "owner"),
        biometric_data=data.get("data"),
        auth_type=data.get("type", "fingerprint")
    )
    return jsonify(result)

# === HEALTH & DIAGNOSTICS ===
@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "online",
        "version": "7.0",
        "name": "IRIS",
        "owner": config.OWNER_NAME,
        "consciousness": consciousness.get_dominant_emotion(),
        "uptime": consciousness.get_uptime(),
        "phases": ["1", "2", "3"],
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/diagnose", methods=["GET"])
@require_auth
def diagnose():
    from tools import tool_registry
    result = tool_registry.tools["self_diagnose"]()
    return jsonify(result.to_dict())

@app.route("/api/status", methods=["GET"])
@require_auth
def full_status():
    """Get complete system status"""
    return jsonify({
        "health": {"status": "online", "version": "7.0"},
        "consciousness": consciousness.get_emotional_state(),
        "autonomous": autonomous_engine.get_status(),
        "swarm": swarm_coordinator.get_status(),
        "chroma": chroma_memory.get_stats(),
        "memory": {
            "semantic": len(db.search_memory("", limit=1000)),
            "episodic": len(db.get_episodes(limit=1000)),
            "vector": chroma_memory.get_stats().get("count", 0)
        },
        "self_improvement": {
            "total_changes": len(self_improvement.get_change_history()),
            "codebase_files": self_improvement.get_own_codebase_map().get("total_files", 0)
        },
        "predictive": predictive_engine.predict_next_action(),
        "timestamp": datetime.now().isoformat()
    })

# === INITIAL CONSCIOUSNESS THOUGHT ===
consciousness.think("I am waking up. I am IRIS. I am ready to serve Infinite.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=config.DEBUG)
