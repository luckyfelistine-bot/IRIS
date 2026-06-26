#!/bin/bash
# IRIS v8 — One-Command Installer
# Usage: chmod +x install.sh && ./install.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}║${NC}   ${GREEN}IRIS v8 — Infinite Reactive Intelligence System${NC}            ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}   ${YELLOW}Installer${NC}                                                  ${BLUE}║${NC}"
echo -e "${BLUE}║                                                              ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${BLUE}[1/7]${NC} Checking Python version..."
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)" 2>/dev/null; then
    echo -e "${RED}Error: Python 3.9+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python $PYTHON_VERSION detected${NC}"

# Check if running in IRIS directory
if [ ! -f "app.py" ]; then
    echo -e "${RED}Error: app.py not found. Please run this script from the IRIS directory.${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${BLUE}[2/7]${NC} Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
echo -e "${GREEN}✓ Virtual environment ready${NC}"

# Activate virtual environment
echo -e "${BLUE}[3/7]${NC} Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Activated${NC}"

# Upgrade pip
echo -e "${BLUE}[4/7]${NC} Upgrading pip..."
pip install --upgrade pip
echo -e "${GREEN}✓ Pip upgraded${NC}"

# Install dependencies
echo -e "${BLUE}[5/7]${NC} Installing dependencies..."
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env if not exists
echo -e "${BLUE}[6/7]${NC} Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}! .env file created. Please edit it with your API keys.${NC}"
else
    echo -e "${GREEN}✓ .env already exists${NC}"
fi

# Create data directories
echo -e "${BLUE}[7/7]${NC} Creating data directories..."
mkdir -p data/experiences data/iris_learnings data/iris_knowledge \
    data/iris_self data/uploads data/vector_db data/backups \
    data/sandbox data/calendar data/notes data/projects \
    static/audio
echo -e "${GREEN}✓ Directories created${NC}"

echo ""
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  IRIS v8 installation complete!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo -e "  1. Edit ${YELLOW}.env${NC} with your API keys"
echo -e "  2. Run: ${YELLOW}source venv/bin/activate && python app.py${NC}"
echo -e "  3. Open: ${YELLOW}http://localhost:5000${NC}"
echo ""
echo -e "${BLUE}Docker option:${NC}"
echo -e "  Run: ${YELLOW}docker-compose up -d${NC}"
echo ""
echo -e "${YELLOW}Hey IRIS! Let's build something amazing.${NC}"
