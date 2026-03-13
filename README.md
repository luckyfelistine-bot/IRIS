# IRIS v7.0 SECURE – The Conscious AI Workspace

IRIS is a powerful, self‑contained AI workspace with persistent memory, document intelligence, voice interaction, system control, and a built‑in games universe. Built with Flask and modern web technologies, it provides a secure, extensible environment for productivity, creativity, and learning.

![IRIS Logo](static/iris-logo.png) <!-- Replace with your actual logo if you have one -->

## ✨ Features

### 🤖 AI Chat
- Multiple AI **personalities** (Balanced, J.A.R.V.I.S., F.R.I.D.A.Y., Creative, Mentor, Scientist, Companion…)
- **Reasoning modes** (Normal, Deep Analysis, Fast Response, Code Only, Silent Tools)
- Powered by Groq’s ultra‑fast LLMs (Llama 3.3‑70B, Llama 3.1‑8B) with automatic fallback to local Ollama

### 📄 Document Intelligence
- Upload **any document** (PDF, Word, Excel, PowerPoint, images, code, archives)
- Automatic **OCR** for scanned PDFs and images (requires Tesseract)
- **Summarisation** (AI‑powered or extractive fallback)
- **Q&A** – ask questions about document content
- **Translation** between 15+ languages
- **Named entity recognition** (people, organisations, dates, etc.) via Stanza or regex
- **Sentiment analysis** (positive/negative/neutral)
- **Compare** two documents

### 🎤 Voice Interaction
- **Speak** to IRIS – click the microphone button
- **Listen** to responses – choose from 10+ natural‑sounding voice profiles (Jarvis, Friday, Sarah, etc.)
- **Live mode** – continuous voice conversation with hologram animation

### 🧠 Persistent Memory
- IRIS automatically learns facts from your conversations
- View, edit, and confirm pending facts in the Memory panel
- Facts persist across chats and help personalise responses

### 🕹️ Maflex Games Universe
- Built‑in games: Tic‑Tac‑Toe, Chess, Connect Four, Hangman, Blackjack, and more
- **Energy‑based power system** – use special abilities (Insight, Manifest, Avatar…)
- AI buddy that comments on your gameplay

### 🔧 System Control
- Take **screenshots**
- **Lock** your computer
- Monitor **CPU**, **RAM**, and uptime
- Adjust **volume** and **brightness** (OS‑dependent)
- Shutdown or restart your machine (with caution)

### 👑 Creator Admin
- Manage users – list, view facts/documents, impersonate, export/delete
- **Self‑destruct** – erase all your data and receive a backup by email
- Schedule reports and reminders

### 🎨 Themes & UI
- 6 beautiful themes: Midnight, Deep Ocean, Sunset Glow, Forest Night, Clean Light, System Auto
- Collapsible sidebar, command palette (Ctrl+K), toast notifications, typing indicators
- Fully responsive design

### 🔒 Security
- Environment‑based secrets (no hardcoded keys)
- CSRF protection on all state‑changing operations
- Input sanitisation (HTML escaping, bleach)
- SQL injection prevention (parameterised queries)
- XSS protection headers
- Audit logging of all sensitive actions

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/iris.git
cd iris
```

### 2. Set up a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate      # Linux/macOS
venv\Scripts\activate         # Windows
```

### 3. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 4. Install system dependencies (optional but highly recommended)

#### Tesseract OCR (for document OCR)
- **Windows**: Download from [UB‑Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) (64‑bit recommended).  
  After installation, set the path in `documentation.py`:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```
- **macOS**: `brew install tesseract`
- **Linux**: `sudo apt install tesseract-ocr`

#### Ollama (optional, for local LLM fallback)
- Download from [ollama.ai](https://ollama.ai) and run a model like `llama3.2`

### 5. Configure environment variables
Create a `.env` file in the project root (see `.env.example`):
```
FLASK_SECRET_KEY=your-secret-key-here                     # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
GROQ_API_KEY_PRIMARY=your-groq-api-key                    # Get from console.groq.com
GROQ_API_KEY_SECONDARY=your-second-key                    # Optional, for fast models
CREATOR_USERNAME=your-creator-username                    # Will be granted admin role
CREATOR_ADMIN_PASSWORD=your-creator-password              # Used for authentication and self‑destruct
```

### 6. Run the application
```bash
python app.py
```
Then open http://localhost:5000 in your browser.

## 🎮 Usage

### First login
- Enter any username – a new user is created automatically.
- If you use the **creator username** you set in `.env`, you’ll get admin privileges.

### Start a conversation
- Type a message and press Enter.
- Use `/help` to see all available commands.
- Use Ctrl+K to open the command palette.

### Upload a document
- Drag and drop a file onto the message input area, or click the paperclip icon.
- Supported formats: `.txt`, `.md`, `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.png`, `.jpg`, `.gif`, `.py`, `.js`, `.html`, `.css`, `.json`, `.csv`, `.zip` (contents listed), and many more.
- After upload, a system message appears with a summary and interactive options.

### Use voice
- Click the microphone button and speak.
- When IRIS responds, a speaking indicator appears – click the pause button to stop.

### Explore memory
- Open the right panel (toggle with the columns icon) and go to the **Memory** tab.
- See pending facts, confirmed facts, and a memory graph.
- Add, edit, or delete facts manually.

### Play games
- Click the infinity (∞) button to enter the **Maflex Universe**.
- Start a game, use commands like `/move` or `/use power`, and watch the AI respond.

### Creator admin
- If you’re logged in as creator, an **Admin** tab appears in the right panel.
- Manage users, view their data, impersonate, export, or delete.
- The **Danger Zone** at the bottom of the Settings panel allows self‑destruct (erases all your data and emails a backup).

## 🔧 Configuration

Key environment variables:

| Variable | Description |
|----------|-------------|
| `FLASK_SECRET_KEY` | Used for session signing. Generate with `secrets.token_hex(32)`. |
| `GROQ_API_KEY_PRIMARY` | Your Groq API key (primary, used for most models). |
| `GROQ_API_KEY_SECONDARY` | Optional second key for fast models. |
| `CREATOR_USERNAME` | Username that will be granted creator role. |
| `CREATOR_ADMIN_PASSWORD` | Password for creator authentication. |
| `DATABASE_URL` | SQLite database path (default: `sqlite:///iris_secure_v7.db`). |
| `MAX_CONTENT_LENGTH` | Maximum upload size (default 50MB). |
| `ENABLE_CSRF` | Set to `False` to disable CSRF (not recommended). |

## 📁 Project Structure

```
iris/
├── app.py                      # Main Flask application
├── skills/                      # Backend modules
│   ├── documentation.py         # Document intelligence (OCR, summarisation, Q&A…)
│   ├── smart_memory.py          # Persistent memory system
│   ├── voice_system.py          # TTS and speech recognition
│   ├── games.py                 # Maflex games engine (legacy)
│   ├── maflex_games.py          # Maflex v3 games universe
│   ├── email_reporter.py        # Scheduled email reports
│   └── security.py              # Password hashing utilities
├── static/
│   ├── css/
│   │   └── iris-theme.css       # All styles and themes
│   └── js/
│       └── iris-app.js          # Frontend application logic
├── templates/
│   └── index.html               # Main page
├── docs/                         # Uploaded document storage
├── exports/                      # Exported files (chats, backups)
├── logs/                         # Application logs
├── charts/                       # Generated chart images
├── uploads/                      # User avatar uploads
├── .env.example                  # Example environment variables
├── requirements.txt
└── README.md
```

## 📡 API Endpoints (Selected)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/user` | Get current user |
| PUT    | `/api/user/settings` | Update user settings |
| POST   | `/api/login` | Login (creates user if not exists) |
| GET    | `/api/chats` | List chats |
| POST   | `/api/chats` | Create new chat |
| GET    | `/api/chats/<id>/messages` | Get messages |
| POST   | `/api/chats/<id>/messages` | Send a message |
| POST   | `/api/documents` | Upload a document |
| GET    | `/api/documents` | List documents |
| GET    | `/api/documents/<id>` | Get document details |
| POST   | `/api/documents/<id>/summarize` | Summarise document |
| POST   | `/api/documents/<id>/ask` | Ask a question about a document |
| GET    | `/api/documents/<id>/entities` | Extract named entities |
| POST   | `/api/voice/listen` | Transcribe microphone input |
| POST   | `/api/voice/speak` | Speak text |
| GET    | `/api/system/status` | Get system stats |
| POST   | `/api/system/screenshot` | Take a screenshot |
| GET    | `/api/admin/users` | List all users (creator only) |

## 🐛 Troubleshooting

### Upload fails with “MIME type mismatch: …”
- Add the detected MIME type to the `MIME_TYPES` dictionary in `documentation.py`. For example:
  ```python
  'application/CDFV2': ['ppt'],
  ```

### OCR not working
- Ensure Tesseract is installed and the path is correctly set in `documentation.py`:
  ```python
  pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
  ```
- Test with `tesseract --version` in your terminal.

### Voice not working
- Install `edge-tts`: `pip install edge-tts`
- For microphone input, you need `pyaudio`. On Windows, use a pre‑built wheel:
  ```bash
  pip install pipwin
  pipwin install pyaudio
  ```
- On Linux, you may need `portaudio` development libraries.

### Memory error `NOT NULL constraint failed: smart_memories.user_id`
- This is a known issue with the `smart_memory` table. A fix is coming soon. As a workaround, you can disable memory by commenting out the relevant code in `app.py` inside `send_message()`.

### “Documentation system failed to load” on startup
- Check the full traceback – usually a missing dependency or an import error.
- Ensure you have installed all packages from `requirements.txt`.
- On Python 3.14, spaCy may fail; you can safely remove `spacy` from `requirements.txt` – the system falls back to stanza and regex.

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## 📄 License

MIT License – see the [LICENSE](LICENSE) file.

## 🙌 Acknowledgements

- [Groq](https://groq.com) for lightning‑fast LLM inference.
- [Hugging Face](https://huggingface.co) for transformer models.
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) for optical character recognition.
- [Stanza](https://stanfordnlp.github.io/stanza/) from the Stanford NLP Group.
- [Flask](https://flask.palletsprojects.com/) and all the other amazing open‑source libraries.

---

**Built with ❤️ by [INFINITE VYBEFLIX]**
```

Now, here is the complete `requirements.txt` file:

```txt
# IRIS v7.0 SECURE - Python Dependencies
# Install with: pip install -r requirements.txt

# Core Flask & Security
Flask>=3.0.0
Flask-CORS>=4.0.0
Flask-WTF>=1.2.0
python-dotenv>=1.0.0
Werkzeug>=3.0.0
bleach>=6.0.0                    # For HTML sanitization

# Database & Scheduling
APScheduler>=3.10.0

# AI & Language Models
groq>=0.9.0                       # Groq API client
transformers>=4.30.0              # For summarization & sentiment analysis
torch>=2.0.0                       # Required by transformers (large, optional)
stanza>=1.6.0                      # Optional NER (fallback if spacy fails)
spacy>=3.7.0                        # Optional NER (may have Python 3.14 issues)
deep-translator>=1.11.0            # For document translation

# Document Processing
pdfplumber>=0.10.0                 # PDF text extraction
pytesseract>=0.3.10                 # OCR (requires Tesseract system install)
Pillow>=10.0.0                      # Image processing for OCR & thumbnails
pdf2image>=1.16.0                   # Convert PDF pages to images for OCR
PyPDF2>=3.0.0                       # Fallback PDF extraction
python-magic-bin>=0.4.14            # MIME type detection (Windows binary)
# For Linux/macOS use: python-magic>=0.4.27

# Voice
edge-tts>=6.1.0                     # Text-to-speech (optional)
# For speech recognition you may need additional packages (e.g., SpeechRecognition, pyaudio)

# System Monitoring & Automation
psutil>=5.9.0                       # System stats (optional)
pyautogui>=0.9.54                   # Screenshots, system control (optional)

# Data Visualization
matplotlib>=3.8.0                   # Chart generation (optional)
numpy>=1.24.0                       # Numerical operations (optional)

# Utilities
requests>=2.31.0
```