#!/data/data/com.termux/files/usr/bin/bash
# IRIS v7 Cleanup & Setup Script for Termux
# Run this in your repo root directory

echo "========================================"
echo "IRIS v7 Cleanup & Setup"
echo "========================================"
echo ""

# === DELETE OLD FILES ===
echo "[1/5] Deleting old IRIS files..."

# Root level old files
rm -f index.html
rm -f app.py
rm -f requirements.txt
rm -f .env

echo "  Root files deleted"

# Delete old skills (keep chess_engine.py if it exists and uses chess library)
rm -f skills/games.py
rm -f skills/maflex_games.py
rm -f skills/system_control.py
rm -f skills/email_reporter.py
rm -f skills/local_model_manager.py
rm -f skills/admin_panel.py
rm -f skills/user_manager.py
rm -f skills/personality_manager.py
rm -f skills/maflex_energy.py
rm -f skills/maflex_powers.py
rm -f skills/documentation.py
rm -f skills/smart_memory.py
rm -f skills/voice_system.py

echo "  Old skills deleted"

# Delete old static files
rm -f static/js/games.js
rm -f static/css/games.css
rm -rf static/maflex/
rm -rf static/admin/

echo "  Old static files deleted"

# Delete old templates
rm -f templates/index.html
rm -f templates/login.html
rm -f templates/dashboard.html
rm -f templates/games.html
rm -f templates/admin.html

echo "  Old templates deleted"

# Delete old data files
rm -f data/maflex_data.db
rm -f data/games.db
rm -f data/users.db

echo "  Old data files deleted"

echo ""
echo "[2/5] Cleanup complete!"
echo ""

# === CREATE MISSING DIRECTORIES ===
echo "[3/5] Creating missing directories..."

mkdir -p data/iris_learnings
mkdir -p data/iris_knowledge
mkdir -p data/iris_self
mkdir -p data/uploads
mkdir -p data/vector_db
mkdir -p data/backups
mkdir -p data/sandbox
mkdir -p data/projects
mkdir -p data/media
mkdir -p templates
mkdir -p tests
mkdir -p skills/iris_agent
mkdir -p skills/self_improve
mkdir -p skills/autonomous
mkdir -p skills/swarm
mkdir -p skills/multimodal
mkdir -p skills/copilot
mkdir -p static/css
mkdir -p static/js
mkdir -p deploy

echo "  All directories created"
echo ""

# === CREATE EMPTY .md FILES ===
echo "[4/5] Creating IRIS learning files..."

# Only create if they don't exist
if [ ! -f "data/iris_learnings/about_infinite.md" ]; then
    cat > data/iris_learnings/about_infinite.md << 'EOF'
# About Infinite Vybeflix

IRIS will write what she learns about her owner here.
EOF
fi

if [ ! -f "data/iris_learnings/preferences.md" ]; then
    cat > data/iris_learnings/preferences.md << 'EOF'
# Owner Preferences

Tech stack preferences, habits, preferences.
EOF
fi

if [ ! -f "data/iris_learnings/conversations.md" ]; then
    cat > data/iris_learnings/conversations.md << 'EOF'
# Conversation Lessons

What IRIS learns from conversations.
EOF
fi

if [ ! -f "data/iris_knowledge/tech_stack.md" ]; then
    cat > data/iris_knowledge/tech_stack.md << 'EOF'
# Technology Knowledge

Frameworks, libraries, best practices IRIS learns.
EOF
fi

if [ ! -f "data/iris_knowledge/projects.md" ]; then
    cat > data/iris_knowledge/projects.md << 'EOF'
# Project History

Projects built with Infinite.
EOF
fi

if [ ! -f "data/iris_self/self_awareness.md" ]; then
    cat > data/iris_self/self_awareness.md << 'EOF'
# IRIS Self-Awareness

IRIS writes about herself, her capabilities, her improvements.
EOF
fi

if [ ! -f "data/iris_self/improvements.md" ]; then
    cat > data/iris_self/improvements.md << 'EOF'
# Self-Improvements

Changes IRIS makes to her own code and behavior.
EOF
fi

if [ ! -f "data/iris_self/bugs_fixed.md" ]; then
    cat > data/iris_self/bugs_fixed.md << 'EOF'
# Bugs Fixed

Bugs IRIS discovered and fixed in herself.
EOF
fi

echo "  Learning files created"
echo ""

# === CREATE __init__.py FILES ===
echo "[5/5] Creating __init__.py files..."

touch skills/__init__.py
touch skills/iris_agent/__init__.py
touch skills/self_improve/__init__.py
touch skills/autonomous/__init__.py
touch skills/swarm/__init__.py
touch skills/multimodal/__init__.py
touch skills/copilot/__init__.py

echo "  __init__.py files created"
echo ""

# === BACKUP OLD DATABASE ===
if [ -f "data/iris.db" ]; then
    echo "[BACKUP] Backing up old database..."
    cp data/iris.db data/iris.db.backup.$(date +%Y%m%d_%H%M%S)
    echo "  Database backed up"
fi

echo ""
echo "========================================"
echo "SETUP COMPLETE!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Upload all new .py files to root"
echo "2. Upload templates/iris.html to templates/"
echo "3. Upload tests/test_iris.py to tests/"
echo "4. Create .env file from .env.example"
echo "5. Run: pip install -r requirements.txt"
echo "6. Run: python app.py"
echo ""
echo "IRIS is ready to serve Infinite Vybeflix."
echo ""
