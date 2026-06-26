"""IRIS v8 Main Application — Flask Backend with All Endpoints"""
import os
import json
import uuid
import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, session, Response, stream_with_context
from flask_cors import CORS
from config import config
from core.db import db
from core.orchestrator import orchestrator
from core.aevibron_client import aevibron
from core.models import ReasoningPlan
from core.tool_registry import tool_registry
from core.memory_engine import memory_engine
from core.predictive_engine import predictive_engine
from modules.consciousness import consciousness
from modules.security import security_manager
from modules.wake_word import wake_word_detector
from modules.phone_bridge import phone_bridge
from modules.vision_stream import vision_stream
from modules.voice_system import voice_system
from modules.autonomous import autonomous_engine
from modules.project_generator import project_generator
from modules.mobile_api import mobile_api
from skills.calendar_skill import calendar_skill
from skills.notes_skill import notes_skill
from skills.math_skill import math_skill
from modules.email_module import email_module
from modules.news_module import news_module
from modules.sports_module import sports_module
from modules.image_module import image_module
from modules.voicerss_module import voicerss_module


app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = config.FLASK_SECRET_KEY
CORS(app)

# Start autonomous engine
autonomous_engine.start()

# ============ AUTHENTICATION ============

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    password = data.get('password', '')
    device_fingerprint = data.get('device_fingerprint')

    if security_manager.verify_password(password):
        session_id = security_manager.create_session()
        return jsonify({"success": True, "session_id": session_id, "message": "Welcome back, Infinite"})
    elif device_fingerprint and security_manager.verify_device_fingerprint(device_fingerprint):
        session_id = security_manager.create_session()
        return jsonify({"success": True, "session_id": session_id, "message": "Welcome back, Infinite"})
    return jsonify({"success": False, "error": "Invalid credentials"}), 401

@app.route('/api/auth/verify', methods=['POST'])
def verify_session():
    data = request.get_json() or {}
    session_id = data.get('session_id')
    if security_manager.validate_session(session_id):
        return jsonify({"success": True, "valid": True})
    return jsonify({"success": False, "valid": False}), 401

# ============ MAIN CHAT ============

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    user_input = data.get('message', '')
    session_id = data.get('session_id') or session.get('session_id') or str(uuid.uuid4())

    if not user_input:
        return jsonify({"success": False, "error": "No message provided"}), 400

    # Save user message
    db.save_message(session_id, "user", user_input)

    # Check for skills first
    matching_skill = memory_engine.find_matching_skill(user_input)
    if matching_skill:
        plan = memory_engine.apply_skill(matching_skill, user_input)
    else:
        # Let orchestrator handle it
        plan = None

    # Get predictive context
    predictive_engine.record_interaction(user_input, [], True)
    context = predictive_engine.prewarm_context(user_input)

    # Process with orchestrator
    results = []
    for update in orchestrator.process(user_input, session_id):
        if update.get("final"):
            final = update
        else:
            results.append(update)

    # Save assistant response
    response_text = final.get("message", "Processing...")
    db.save_message(session_id, "assistant", response_text,
                    reasoning=json.dumps(final.get("data", {}).get("plan", {})),
                    tool_calls=final.get("data", {}).get("tools_used", []))

    # Update consciousness
    consciousness.on_event("user_message", {"input": user_input})

    return jsonify({
        "success": True,
        "response": response_text,
        "session_id": session_id,
        "status_updates": results,
        "verification": final.get("data", {}).get("verification"),
        "emotion": consciousness.get_dominant_emotion()
    })

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    data = request.get_json() or {}
    user_input = data.get('message', '')
    session_id = data.get('session_id') or str(uuid.uuid4())

    def generate():
        for update in orchestrator.process(user_input, session_id):
            yield f"data: {json.dumps(update)}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream')

# ============ VOICE ============

@app.route('/api/voice/speak', methods=['POST'])
def voice_speak():
    data = request.get_json() or {}
    text = data.get('text', '')
    emotion = data.get('emotion', 'neutral')

    if not text:
        return jsonify({"success": False, "error": "No text provided"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(voice_system.speak(text, emotion))
    loop.close()

    return jsonify(result)

@app.route('/api/voice/listen', methods=['POST'])
def voice_listen():
    result = voice_system.listen()
    return jsonify(result)

@app.route('/api/voice/wake-word/start', methods=['POST'])
def start_wake_word():
    wake_word_detector.start_listening()
    return jsonify({"success": True, "message": "Wake word listener started"})

@app.route('/api/voice/wake-word/stop', methods=['POST'])
def stop_wake_word():
    wake_word_detector.stop_listening()
    return jsonify({"success": True, "message": "Wake word listener stopped"})

# ============ VISION ============

@app.route('/api/vision/capture', methods=['POST'])
def vision_capture():
    data = request.get_json() or {}
    source = data.get('source', 'screen')
    if source == 'screen':
        frame = vision_stream.capture_screen()
    else:
        frame = vision_stream.capture_camera()
    return jsonify({"success": frame is not None, "frame": frame})

@app.route('/api/vision/stream/start', methods=['POST'])
def vision_stream_start():
    data = request.get_json() or {}
    source = data.get('source', 'screen')
    interval = data.get('interval', 2.0)
    vision_stream.start_stream(source, interval)
    return jsonify({"success": True, "message": f"Vision stream started: {source}"})

@app.route('/api/vision/stream/stop', methods=['POST'])
def vision_stream_stop():
    vision_stream.stop_stream()
    return jsonify({"success": True, "message": "Vision stream stopped"})

@app.route('/api/vision/analyze', methods=['POST'])
def vision_analyze():
    data = request.get_json() or {}
    question = data.get('question', 'What do you see?')
    result = vision_stream.analyze_current_view(question)
    return jsonify(result)

# ============ PHONE BRIDGE ============

@app.route('/api/phone/contacts', methods=['GET'])
def phone_contacts():
    result = phone_bridge.get_contacts()
    return jsonify(result)

@app.route('/api/phone/contacts/search', methods=['GET'])
def phone_search_contacts():
    query = request.args.get('q', '')
    result = phone_bridge.search_contacts(query)
    return jsonify(result)

@app.route('/api/phone/call', methods=['POST'])
def phone_call():
    data = request.get_json() or {}
    number = data.get('number', '')
    result = phone_bridge.call_contact(number)
    return jsonify(result)

@app.route('/api/phone/messages', methods=['GET'])
def phone_messages():
    limit = request.args.get('limit', 20, type=int)
    result = phone_bridge.get_messages(limit)
    return jsonify(result)

@app.route('/api/phone/send-message', methods=['POST'])
def phone_send_message():
    data = request.get_json() or {}
    number = data.get('number', '')
    text = data.get('text', '')
    result = phone_bridge.send_message(number, text)
    return jsonify(result)

@app.route('/api/phone/torch', methods=['POST'])
def phone_torch():
    data = request.get_json() or {}
    state = data.get('state', 'toggle')
    result = phone_bridge.torch(state)
    return jsonify(result)

@app.route('/api/phone/wifi', methods=['POST'])
def phone_wifi():
    data = request.get_json() or {}
    state = data.get('state', 'toggle')
    result = phone_bridge.toggle_wifi(state)
    return jsonify(result)

@app.route('/api/phone/bluetooth', methods=['POST'])
def phone_bluetooth():
    data = request.get_json() or {}
    state = data.get('state', 'toggle')
    result = phone_bridge.toggle_bluetooth(state)
    return jsonify(result)

@app.route('/api/phone/battery', methods=['GET'])
def phone_battery():
    result = phone_bridge.get_battery()
    return jsonify(result)

@app.route('/api/phone/notifications', methods=['GET'])
def phone_notifications():
    result = phone_bridge.get_notifications()
    return jsonify(result)

@app.route('/api/phone/camera', methods=['POST'])
def phone_camera():
    data = request.get_json() or {}
    action = data.get('action', 'open')
    if action == 'open':
        result = phone_bridge.open_camera()
    elif action == 'take_photo':
        result = phone_bridge.take_photo()
    else:
        result = {"success": False, "error": "Unknown action"}
    return jsonify(result)

@app.route('/api/phone/screenshot', methods=['GET'])
def phone_screenshot():
    result = phone_bridge.screenshot()
    return jsonify(result)

@app.route('/api/phone/device-info', methods=['GET'])
def phone_device_info():
    result = phone_bridge.get_device_info()
    return jsonify(result)

# ============ CALENDAR ============

@app.route('/api/calendar/events', methods=['GET'])
def calendar_get_events():
    start = request.args.get('start')
    end = request.args.get('end')
    category = request.args.get('category')
    result = calendar_skill.get_events(start, end, category)
    return jsonify(result)

@app.route('/api/calendar/events', methods=['POST'])
def calendar_add_event():
    data = request.get_json() or {}
    title = data.get('title', '')
    start_time = data.get('start_time', '')
    if not title or not start_time:
        return jsonify({"success": False, "error": "Title and start_time required"}), 400

    result = calendar_skill.add_event(
        title=title,
        start_time=start_time,
        end_time=data.get('end_time'),
        description=data.get('description'),
        location=data.get('location'),
        category=data.get('category', 'general'),
        priority=data.get('priority', 5),
        recurring=data.get('recurring')
    )
    return jsonify(result)

@app.route('/api/calendar/events/<int:event_id>', methods=['DELETE'])
def calendar_delete_event(event_id):
    result = calendar_skill.delete_event(event_id)
    return jsonify(result)

@app.route('/api/calendar/today', methods=['GET'])
def calendar_today():
    result = calendar_skill.get_today()
    return jsonify(result)

@app.route('/api/calendar/upcoming', methods=['GET'])
def calendar_upcoming():
    hours = request.args.get('hours', 24, type=int)
    result = calendar_skill.get_upcoming(hours)
    return jsonify(result)

@app.route('/api/calendar/parse', methods=['POST'])
def calendar_parse():
    data = request.get_json() or {}
    text = data.get('text', '')
    result = calendar_skill.parse_natural_date(text)
    return jsonify(result)

@app.route('/api/calendar/export', methods=['GET'])
def calendar_export():
    ics = calendar_skill.export_to_ics()
    return Response(ics, mimetype='text/calendar', headers={'Content-Disposition': 'attachment; filename=iris_calendar.ics'})

# ============ NOTES ============

@app.route('/api/notes', methods=['GET'])
def notes_get():
    category = request.args.get('category')
    search = request.args.get('search')
    result = notes_skill.get_notes(category, search)
    return jsonify(result)

@app.route('/api/notes', methods=['POST'])
def notes_create():
    data = request.get_json() or {}
    title = data.get('title', '')
    if not title:
        return jsonify({"success": False, "error": "Title required"}), 400
    result = notes_skill.create_note(
        title=title,
        content=data.get('content', ''),
        category=data.get('category', 'general'),
        tags=data.get('tags', [])
    )
    return jsonify(result)

@app.route('/api/notes/<int:note_id>', methods=['GET'])
def notes_get_one(note_id):
    result = notes_skill.get_note(note_id)
    return jsonify(result)

@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def notes_update(note_id):
    data = request.get_json() or {}
    result = notes_skill.update_note(
        note_id=note_id,
        title=data.get('title'),
        content=data.get('content'),
        category=data.get('category'),
        tags=data.get('tags')
    )
    return jsonify(result)

@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def notes_delete(note_id):
    result = notes_skill.delete_note(note_id)
    return jsonify(result)

@app.route('/api/notes/<int:note_id>/pin', methods=['POST'])
def notes_pin(note_id):
    data = request.get_json() or {}
    pinned = data.get('pinned', True)
    result = notes_skill.pin_note(note_id, pinned)
    return jsonify(result)

@app.route('/api/notes/quick', methods=['POST'])
def notes_quick():
    data = request.get_json() or {}
    text = data.get('text', '')
    result = notes_skill.quick_note(text)
    return jsonify(result)

# ============ MATH ============

@app.route('/api/math/solve', methods=['POST'])
def math_solve():
    data = request.get_json() or {}
    expression = data.get('expression', '')
    variable = data.get('variable', 'x')
    result = math_skill.solve(expression, variable)
    return jsonify(result)

@app.route('/api/math/simplify', methods=['POST'])
def math_simplify():
    data = request.get_json() or {}
    expression = data.get('expression', '')
    result = math_skill.simplify(expression)
    return jsonify(result)

@app.route('/api/math/differentiate', methods=['POST'])
def math_differentiate():
    data = request.get_json() or {}
    expression = data.get('expression', '')
    variable = data.get('variable', 'x')
    order = data.get('order', 1)
    result = math_skill.differentiate(expression, variable, order)
    return jsonify(result)

@app.route('/api/math/integrate', methods=['POST'])
def math_integrate():
    data = request.get_json() or {}
    expression = data.get('expression', '')
    variable = data.get('variable', 'x')
    limits = data.get('limits')
    result = math_skill.integrate(expression, variable, limits)
    return jsonify(result)

@app.route('/api/math/evaluate', methods=['POST'])
def math_evaluate():
    data = request.get_json() or {}
    expression = data.get('expression', '')
    result = math_skill.evaluate(expression)
    return jsonify(result)

@app.route('/api/math/statistics', methods=['POST'])
def math_statistics():
    data = request.get_json() or {}
    values = data.get('values', [])
    operation = data.get('operation', 'all')
    result = math_skill.statistics(values, operation)
    return jsonify(result)

@app.route('/api/math/convert', methods=['POST'])
def math_convert():
    data = request.get_json() or {}
    value = data.get('value', 0)
    from_unit = data.get('from', '')
    to_unit = data.get('to', '')
    result = math_skill.convert_units(value, from_unit, to_unit)
    return jsonify(result)

# ============ PROJECT GENERATOR ============

@app.route('/api/projects/generate', methods=['POST'])
def projects_generate():
    data = request.get_json() or {}
    name = data.get('name', '')
    template = data.get('template', 'nextjs')
    description = data.get('description', '')
    if not name:
        return jsonify({"success": False, "error": "Project name required"}), 400
    result = project_generator.generate_project(name, template, description)
    return jsonify(result)

@app.route('/api/projects/deploy', methods=['POST'])
def projects_deploy():
    data = request.get_json() or {}
    name = data.get('name', '')
    repo_name = data.get('repo_name')
    deploy_to_vercel = data.get('deploy_to_vercel', True)
    if not name:
        return jsonify({"success": False, "error": "Project name required"}), 400
    result = project_generator.deploy_project(name, repo_name, deploy_to_vercel)
    return jsonify(result)

@app.route('/api/projects', methods=['GET'])
def projects_list():
    projects = project_generator.get_projects()
    return jsonify({"success": True, "projects": projects})

@app.route('/api/projects/templates', methods=['GET'])
def projects_templates():
    templates = project_generator.get_available_templates()
    return jsonify({"success": True, "templates": templates})

# ============ SELF-IMPROVEMENT ============

@app.route('/api/self/analyze', methods=['GET'])
def self_analyze():
    from modules.self_improve import self_improvement
    result = self_improvement.analyze_self()
    return jsonify(result)

@app.route('/api/self/fix', methods=['POST'])
def self_fix():
    from modules.self_improve import self_improvement
    data = request.get_json() or {}
    file_path = data.get('file_path', '')
    old_text = data.get('old_text', '')
    new_text = data.get('new_text', '')
    result = self_improvement.apply_fix(file_path, old_text, new_text)
    return jsonify(result.dict())

@app.route('/api/self/codebase', methods=['GET'])
def self_codebase():
    from modules.self_improve import self_improvement
    result = self_improvement.get_own_codebase_map()
    return jsonify(result)

@app.route('/api/self/history', methods=['GET'])
def self_history():
    from modules.self_improve import self_improvement
    result = self_improvement.get_change_history()
    return jsonify({"success": True, "changes": result})

# ============ CONSCIOUSNESS ============

@app.route('/api/consciousness/state', methods=['GET'])
def consciousness_state():
    return jsonify(consciousness.get_emotional_state())

@app.route('/api/consciousness/think', methods=['GET'])
def consciousness_think():
    trigger = request.args.get('trigger')
    thought = consciousness.think(trigger)
    return jsonify({"success": True, "thought": thought})

@app.route('/api/consciousness/reflect', methods=['GET'])
def consciousness_reflect():
    reflection = consciousness.reflect()
    return jsonify({"success": True, "reflection": reflection})

@app.route('/api/consciousness/identity', methods=['GET'])
def consciousness_identity():
    return jsonify({"success": True, "identity": consciousness.get_identity_statement()})

@app.route('/api/consciousness/thoughts', methods=['GET'])
def consciousness_thoughts():
    limit = request.args.get('limit', 10, type=int)
    thoughts = consciousness.get_recent_thoughts(limit)
    return jsonify({"success": True, "thoughts": thoughts})

# ============ MEMORY ============

@app.route('/api/memory/learn', methods=['POST'])
def memory_learn():
    data = request.get_json() or {}
    key = data.get('key', '')
    value = data.get('value', '')
    category = data.get('category', 'general')
    importance = data.get('importance', 5)
    if not key or not value:
        return jsonify({"success": False, "error": "Key and value required"}), 400
    result = memory_engine.learn(key, value, category, importance)
    return jsonify({"success": result})

@app.route('/api/memory/recall', methods=['GET'])
def memory_recall():
    query = request.args.get('q', '')
    category = request.args.get('category')
    limit = request.args.get('limit', 10, type=int)
    results = memory_engine.recall(query, category, limit)
    return jsonify({"success": True, "results": results})

# ============ AUTONOMOUS ============

@app.route('/api/autonomous/status', methods=['GET'])
def autonomous_status():
    return jsonify(autonomous_engine.get_status())

@app.route('/api/autonomous/queue', methods=['POST'])
def autonomous_queue():
    data = request.get_json() or {}
    description = data.get('description', '')
    priority = data.get('priority', 5)
    task_type = data.get('type', 'general')
    if not description:
        return jsonify({"success": False, "error": "Description required"}), 400
    task_id = autonomous_engine.queue_task(description, priority, task_type=task_type)
    return jsonify({"success": True, "task_id": task_id})

@app.route('/api/autonomous/schedule', methods=['POST'])
def autonomous_schedule():
    data = request.get_json() or {}
    description = data.get('description', '')
    run_at = data.get('run_at', '')
    if not description or not run_at:
        return jsonify({"success": False, "error": "Description and run_at required"}), 400
    try:
        run_at_dt = datetime.fromisoformat(run_at)
        task_id = autonomous_engine.schedule_task(description, run_at_dt)
        return jsonify({"success": True, "task_id": task_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

# ============ MOBILE API ============

@app.route('/api/mobile/register', methods=['POST'])
def mobile_register():
    data = request.get_json() or {}
    device_id = data.get('device_id', '')
    device_type = data.get('device_type', 'android')
    push_token = data.get('push_token')
    if not device_id:
        return jsonify({"success": False, "error": "device_id required"}), 400
    result = mobile_api.register_device(device_id, device_type, push_token)
    return jsonify(result)

@app.route('/api/mobile/status', methods=['POST'])
def mobile_status():
    data = request.get_json() or {}
    device_id = data.get('device_id', '')
    battery = data.get('battery_level')
    location = data.get('location')
    result = mobile_api.update_device_status(device_id, battery, location)
    return jsonify(result)

@app.route('/api/mobile/devices', methods=['GET'])
def mobile_devices():
    devices = mobile_api.get_all_devices()
    return jsonify({"success": True, "devices": devices})

@app.route('/api/mobile/notify', methods=['POST'])
def mobile_notify():
    data = request.get_json() or {}
    device_id = data.get('device_id', '')
    title = data.get('title', '')
    body = data.get('body', '')
    result = mobile_api.send_push_notification(device_id, title, body)
    return jsonify(result)

# ============ TOOLS ============

@app.route('/api/tools', methods=['GET'])
def tools_list():
    return jsonify({"success": True, "tools": tool_registry.schemas})

@app.route('/api/tools/execute', methods=['POST'])
def tools_execute():
    data = request.get_json() or {}
    tool_name = data.get('tool', '')
    params = data.get('params', {})
    if tool_name not in tool_registry.tools:
        return jsonify({"success": False, "error": f"Unknown tool: {tool_name}"}), 400
    result = tool_registry.tools[tool_name](**params)
    return jsonify(result.dict())

# ============ EMAIL ============

@app.route('/api/email/send', methods=['POST'])
def email_send():
    data = request.get_json() or {}
    to = data.get('to', '')
    subject = data.get('subject', '')
    body = data.get('body', '')
    html = data.get('html', False)
    provider = data.get('provider', 'gmail')  # 'gmail' or 'resend'

    if not to or not subject or not body:
        return jsonify({"success": False, "error": "to, subject, and body required"}), 400

    if provider == 'resend':
        result = email_module.send_resend(to, subject, body, html)
    else:
        result = email_module.send_gmail(to, subject, body, html)
    return jsonify(result)

@app.route('/api/email/log-report', methods=['POST'])
def email_log_report():
    data = request.get_json() or {}
    content = data.get('content', '')
    title = data.get('title', 'IRIS Log Report')
    result = email_module.send_log_report(content, title)
    return jsonify(result)

@app.route('/api/email/alert', methods=['POST'])
def email_alert():
    data = request.get_json() or {}
    alert_type = data.get('type', '')
    message = data.get('message', '')
    priority = data.get('priority', 'normal')
    result = email_module.send_alert(alert_type, message, priority)
    return jsonify(result)

# ============ NEWS ============

@app.route('/api/news/latest', methods=['GET'])
def news_latest():
    category = request.args.get('category', 'general')
    limit = request.args.get('limit', 10, type=int)
    result = news_module.get_latest(category, limit)
    return jsonify(result)

@app.route('/api/news/search', methods=['GET'])
def news_search():
    query = request.args.get('q', '')
    limit = request.args.get('limit', 10, type=int)
    result = news_module.search(query, limit)
    return jsonify(result)

@app.route('/api/news/summary', methods=['GET'])
def news_summary():
    category = request.args.get('category', 'general')
    summary = news_module.get_headlines_summary(category)
    return jsonify({"success": True, "summary": summary})

# ============ SPORTS ============

@app.route('/api/sports/live', methods=['GET'])
def sports_live():
    league_id = request.args.get('league_id', type=int)
    result = sports_module.get_live_matches(league_id)
    return jsonify(result)

@app.route('/api/sports/odds', methods=['GET'])
def sports_odds():
    sport = request.args.get('sport', 'soccer')
    region = request.args.get('region', 'us')
    result = sports_module.get_odds(sport, region)
    return jsonify(result)

@app.route('/api/sports/team-stats', methods=['GET'])
def sports_team_stats():
    team_id = request.args.get('team_id', type=int)
    league_id = request.args.get('league_id', type=int)
    season = request.args.get('season', 2024, type=int)
    if not team_id or not league_id:
        return jsonify({"success": False, "error": "team_id and league_id required"}), 400
    result = sports_module.get_team_stats(team_id, league_id, season)
    return jsonify(result)

@app.route('/api/sports/summary', methods=['GET'])
def sports_summary():
    summary = sports_module.get_live_summary()
    return jsonify({"success": True, "summary": summary})

# ============ IMAGE PROCESSING ============

@app.route('/api/image/remove-bg', methods=['POST'])
def image_remove_bg():
    data = request.get_json() or {}
    image_path = data.get('image_path', '')
    output_path = data.get('output_path')
    if not image_path:
        return jsonify({"success": False, "error": "image_path required"}), 400
    result = image_module.remove_background(image_path, output_path)
    return jsonify(result)

@app.route('/api/image/remove-bg-base64', methods=['POST'])
def image_remove_bg_base64():
    data = request.get_json() or {}
    base64_image = data.get('image_base64', '')
    if not base64_image:
        return jsonify({"success": False, "error": "image_base64 required"}), 400
    result = image_module.remove_background_base64(base64_image)
    return jsonify(result)

@app.route('/api/image/resize', methods=['POST'])
def image_resize():
    data = request.get_json() or {}
    image_path = data.get('image_path', '')
    width = data.get('width', 0)
    height = data.get('height', 0)
    if not image_path or not width or not height:
        return jsonify({"success": False, "error": "image_path, width, and height required"}), 400
    result = image_module.resize_image(image_path, width, height)
    return jsonify(result)

@app.route('/api/image/convert', methods=['POST'])
def image_convert():
    data = request.get_json() or {}
    image_path = data.get('image_path', '')
    target_format = data.get('format', 'png')
    if not image_path:
        return jsonify({"success": False, "error": "image_path required"}), 400
    result = image_module.convert_format(image_path, target_format)
    return jsonify(result)

# ============ VOICERSS TTS ============

@app.route('/api/voice/voicerss', methods=['POST'])
def voice_voicerss():
    data = request.get_json() or {}
    text = data.get('text', '')
    language = data.get('language', 'en-us')
    voice = data.get('voice', 'Linda')
    speed = data.get('speed', 0)

    if not text:
        return jsonify({"success": False, "error": "text required"}), 400

    result = voicerss_module.speak(text, language, voice, speed)
    return jsonify(result)

@app.route('/api/voice/voicerss-emotion', methods=['POST'])
def voice_voicerss_emotion():
    data = request.get_json() or {}
    text = data.get('text', '')
    emotion = data.get('emotion', 'neutral')

    if not text:
        return jsonify({"success": False, "error": "text required"}), 400

    result = voicerss_module.speak_with_emotion(text, emotion)
    return jsonify(result)

@app.route('/api/voice/voices', methods=['GET'])
def voice_voices():
    language = request.args.get('language', 'en-us')
    result = voicerss_module.get_voices(language)
    return jsonify(result)

# ============ HEALTH & STATUS ============

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "version": "8.0.0",
        "timestamp": datetime.now().isoformat(),
        "uptime": consciousness.get_uptime(),
        "emotion": consciousness.get_dominant_emotion()
    })

@app.route('/api/status', methods=['GET'])
def status():
    return jsonify({
        "iris": {
            "version": "8.0.0",
            "status": "running",
            "uptime": consciousness.get_uptime(),
            "emotion": consciousness.get_emotional_state(),
            "awareness": consciousness.awareness_level
        },
        "autonomous": autonomous_engine.get_status(),
        "phone_bridge": {"enabled": phone_bridge.enabled, "available": phone_bridge._check_adb()},
        "wake_word": {"available": wake_word_detector.is_available()},
        "vision_stream": {"streaming": vision_stream.is_streaming}
    })

# ============ WEB PAGES ============

@app.route('/')
def index():
    return render_template('iris.html')

@app.route('/voice')
def voice_page():
    return render_template('iris_voice.html')

@app.route('/face')
def face_page():
    return voice_system.get_face_html()

# ============ MAIN ============

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=config.DEBUG)
