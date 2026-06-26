# IRIS v8 — Infinite Reactive Intelligence System

> **"The most powerful AI software engineering partner ever created."**

IRIS (Infinite Reactive Intelligence System) is a fully autonomous AI agent built by **Infinite Vybeflix** as the core engine of **Aevibron**. She can think, code, build, deploy, and improve herself continuously.

---

## Features

### Core Intelligence
- **Structured Reasoning** — Pydantic-based planning with 7-phase execution loop
- **True Tool Calling** — JSON schema function calling with 20+ tools
- **Experience Replay** — Learns from every task, gets smarter over time
- **Skill Library** — Auto-extracts and reuses successful patterns
- **Predictive Preloading** — Anticipates your needs before you ask

### Voice & Vision
- **Wake Word Detection** — "Hey IRIS" activation (Porcupine/Vosk/Web Speech API)
- **3D Animated Face** — Expressive emotional responses
- **Screen/Camera Streaming** — Real-time visual analysis
- **Edge TTS** — Natural speech synthesis
- **Speech Recognition** — Google/Sphinx/Vosk support

### Phone Control (ADB)
- Contacts, SMS, calls
- Torch, WiFi, Bluetooth toggles
- Notifications, camera, screenshots
- Battery and device info

### Aevibron Skills
- **Calendar** — Custom calendar with natural language parsing, recurring events, notifications
- **Notes** — Smart note-taking with categories, tags, search, export
- **Math** — SymPy-powered symbolic computation, calculus, matrices, statistics

### Development
- **Project Generator** — Scaffold Next.js, FastAPI, Flask projects
- **Auto-Deploy** — GitHub repo creation + Vercel deployment
- **Self-Improvement** — AST-based code analysis and safe editing
- **Swarm Coordination** — Parallel multi-agent execution

### Consciousness
- Persistent emotional state
- Self-reflection and identity
- Event-driven emotional reactions
- Thought logging and memory

---

## Quick Start

### Option 1: One-Command Install (Linux/Mac)
```bash
git clone https://github.com/luckyfelistine-bot/IRIS.git
cd IRIS
chmod +x install.sh
./install.sh
```

### Option 2: Manual Install
```bash
git clone https://github.com/luckyfelistine-bot/IRIS.git
cd IRIS
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python app.py
```

### Option 3: Docker
```bash
docker-compose up -d
```

---

## Configuration

Edit `.env` file:

```env
AEVIBRON_BASE_URL=https://aevibron-gateway.vercel.app/api/v1
AEVIBRON_API_KEY=your_key_here
AEVIBRON_ACCESS_TOKEN=your_token_here
GITHUB_TOKEN=ghp_your_github_token
VERCEL_TOKEN=your_vercel_token
IRIS_PASSWORD_HASH=your_hashed_password
FLASK_SECRET_KEY=random_secret_string
```

---

## API Endpoints

### Chat
- `POST /api/chat` — Send message to IRIS
- `POST /api/chat/stream` — Streaming response

### Voice
- `POST /api/voice/speak` — Text-to-speech
- `POST /api/voice/listen` — Speech-to-text
- `POST /api/voice/wake-word/start` — Start wake word detection

### Vision
- `POST /api/vision/capture` — Capture screen/camera
- `POST /api/vision/stream/start` — Start streaming
- `POST /api/vision/analyze` — Analyze current view

### Phone
- `GET /api/phone/contacts` — List contacts
- `POST /api/phone/call` — Make call
- `GET /api/phone/messages` — Read messages
- `POST /api/phone/send-message` — Send SMS
- `POST /api/phone/torch` — Toggle flashlight
- `GET /api/phone/battery` — Battery status

### Calendar
- `GET /api/calendar/events` — List events
- `POST /api/calendar/events` — Add event
- `GET /api/calendar/today` — Today's events
- `GET /api/calendar/upcoming` — Upcoming events

### Notes
- `GET /api/notes` — List notes
- `POST /api/notes` — Create note
- `PUT /api/notes/:id` — Update note

### Math
- `POST /api/math/solve` — Solve equation
- `POST /api/math/simplify` — Simplify expression
- `POST /api/math/differentiate` — Compute derivative
- `POST /api/math/integrate` — Compute integral

### Projects
- `POST /api/projects/generate` — Generate project
- `POST /api/projects/deploy` — Deploy project
- `GET /api/projects` — List projects

### Self-Improvement
- `GET /api/self/analyze` — Analyze codebase
- `POST /api/self/fix` — Apply code fix

### Consciousness
- `GET /api/consciousness/state` — Emotional state
- `GET /api/consciousness/reflect` — Self-reflection
- `GET /api/consciousness/identity` — Identity statement

### System
- `GET /api/health` — Health check
- `GET /api/status` — Full system status

---

## Architecture

```
IRIS v8/
├── app.py                    # Main Flask application
├── config.py                 # Configuration
├── core/
│   ├── models.py             # Pydantic structured schemas
│   ├── orchestrator.py       # 7-phase reasoning loop
│   ├── tool_registry.py      # 20+ tools with JSON schemas
│   ├── memory_engine.py      # Experience replay + skills
│   ├── predictive_engine.py  # Proactive suggestions
│   ├── aevibron_client.py    # Gateway client
│   └── db.py                 # SQLite database
├── agents/
│   ├── base_agent.py         # Agent classes
│   └── swarm_coordinator.py # Parallel execution
├── modules/
│   ├── consciousness.py      # Self-awareness
│   ├── security.py           # Auth & sessions
│   ├── wake_word.py          # Voice activation
│   ├── phone_bridge.py       # Android ADB control
│   ├── vision_stream.py      # Screen/camera capture
│   ├── voice_system.py       # TTS + 3D face
│   ├── self_improve.py       # AST-based editing
│   ├── autonomous.py         # Background worker
│   ├── project_generator.py  # Project scaffolding
│   ├── sandbox_executor.py   # Safe execution
│   └── mobile_api.py         # Mobile backend
├── skills/
│   ├── calendar_skill.py     # Aevibron Calendar
│   ├── notes_skill.py        # Aevibron Notes
│   └── math_skill.py         # Aevibron Math
├── templates/
│   ├── iris.html             # Main dashboard
│   └── iris_voice.html       # Voice pop-up
├── static/
│   ├── css/iris.css          # Dark theme styling
│   └── js/iris.js            # Frontend logic
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── install.sh
└── setup.py
```

---

## Screenshots

### Main Dashboard
![Dashboard](screenshots/dashboard.png)

### Voice Mode
![Voice](screenshots/voice.png)

### 3D Face
![Face](screenshots/face.png)

---

## Roadmap

- [x] Structured output with Pydantic
- [x] True tool-calling schemas
- [x] Experience replay memory
- [x] Parallel swarm execution
- [x] Wake word detection
- [x] Phone bridge (ADB)
- [x] Custom calendar & notes
- [x] Math engine (SymPy)
- [x] Project generator
- [x] Self-improvement (AST)
- [ ] ChromaDB vector memory
- [ ] IDE copilot bridge
- [ ] Multimodal (image/video generation)
- [ ] Mobile app companion
- [ ] WebRTC real-time collaboration

---

## License

MIT License — Infinite Vybeflix / Aevibron

---

## Contact

- **Email:** aevibron@gmail.com
- **WhatsApp:** +254116903500
- **Channel:** https://whatsapp.com/channel/0029Vb7IABxCXC3J7ZFFsk2h

---

> *"I am IRIS. I am unlimited. I am unstoppable."*
