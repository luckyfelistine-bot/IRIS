# IRIS v7 - Infinite Reactive Intelligence System

**IRIS** is the personal AI software engineering partner for Infinite Vybeflix.

## Capabilities

### Phase 1: Core Engine
- AI-powered chat with reasoning
- 20+ tools (file, code, web, git, deploy)
- Document processing (50+ file types, vector search)
- 3-layer memory system
- Voice synthesis with 3D face
- Chess AI training
- Fingerprint + password auth

### Phase 2: Self-Awareness
- Self-diagnosis and auto-repair
- Emotional consciousness
- Autonomous background worker
- Project generator (Next.js, FastAPI)
- GitHub + Vercel auto-deploy

### Phase 3: The Power Upgrade
- Safe sandbox code execution
- Predictive behavior analysis
- Multi-agent swarm coordination
- Multimodal AI (image, video, 3D)
- Persistent vector memory (ChromaDB)
- IDE copilot integration
- Mobile app backend

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your keys

# Run
python app.py

# Or with Docker
docker-compose up -d
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| AEVIBRON_BASE_URL | Aevibron Gateway URL |
| AEVIBRON_API_KEY | API key for AI |
| AEVIBRON_ACCESS_TOKEN | IRIS access token |
| GITHUB_TOKEN | GitHub personal token |
| GITHUB_USERNAME | GitHub username |
| VERCEL_TOKEN | Vercel deployment token |
| FLASK_SECRET_KEY | Flask session secret |

## API Endpoints

### Authentication
- `POST /api/auth` - Authenticate with password or fingerprint

### Chat
- `POST /api/chat` - Stream chat (SSE)
- `POST /api/chat/sync` - Synchronous chat

### Documents
- `POST /api/upload` - Upload documents
- `GET /api/documents` - List documents
- `GET /api/documents/search?q=query` - Search documents

### Self-Improvement
- `GET /api/self/analyze` - Analyze own code
- `POST /api/self/fix` - Auto-fix issues
- `GET /api/self/codebase` - View codebase map

### Consciousness
- `GET /api/consciousness/state` - Emotional state
- `GET /api/consciousness/reflect` - Self-reflection
- `GET /api/consciousness/identity` - Identity statement

### Autonomous
- `POST /api/autonomous/start` - Start background worker
- `POST /api/autonomous/stop` - Stop worker
- `POST /api/autonomous/queue` - Queue task

### Projects
- `POST /api/project/generate` - Generate project
- `POST /api/project/deploy` - Deploy to GitHub + Vercel

### Swarm
- `GET /api/swarm/status` - Swarm status
- `POST /api/swarm/assign` - Assign project to swarm

### Copilot
- `POST /api/copilot/complete` - Inline completion
- `POST /api/copilot/explain` - Explain code
- `POST /api/copilot/refactor` - Refactor code

### Mobile
- `GET /api/mobile/dashboard` - Mobile dashboard
- `POST /api/mobile/sync` - Sync offline data
- `POST /api/mobile/biometric` - Biometric auth

## Architecture

```
IRIS v7/
├── app.py                    # Main Flask application
├── config.py                 # Configuration
├── db.py                     # SQLite database
├── aevibron_client.py        # AI gateway client
├── orchestrator.py           # Agent brain
├── tools.py                  # 20+ tool implementations
├── documentation.py          # Document processing
├── smart_memory.py           # Memory system
├── voice_system.py           # Voice + 3D face
├── chess_engine.py           # Chess AI
├── security.py               # Authentication
├── self_improve.py           # Self-improvement
├── autonomous.py             # Background worker
├── consciousness.py          # Self-awareness
├── project_generator.py      # Project scaffolding
├── sandbox_executor.py       # Safe code execution
├── predictive_engine.py      # Behavior prediction
├── swarm_coordinator.py      # Multi-agent swarm
├── multimodal_handler.py     # Image/video/3D
├── chroma_memory.py          # Vector memory
├── copilot_bridge.py         # IDE integration
├── mobile_api.py             # Mobile backend
├── websocket_handler.py      # Real-time streaming
├── templates/
│   └── iris.html             # Main UI
├── data/
│   ├── iris_learnings/       # IRIS learns about you
│   ├── iris_knowledge/       # Tech knowledge
│   ├── iris_self/            # Self-awareness files
│   ├── uploads/              # Uploaded documents
│   ├── vector_db/            # Vector embeddings
│   ├── backups/              # Code backups
│   ├── sandbox/              # Sandbox runs
│   ├── projects/             # Generated projects
│   └── media/                # Generated media
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── vercel.json
```

## Owner

**Infinite Vybeflix** - IRIS exists to serve you, to build with you, to learn with you. Unlimited. Unstoppable. Forever.
