```markdown
# IRIS Documentation System v7.0 – Enterprise Document Intelligence

The IRIS Documentation System provides comprehensive document management with AI‑powered features: OCR, summarization, Q&A, translation, entity extraction, sentiment analysis, and comparison. It is fully integrated into the IRIS chat interface.

## ✨ Features

- **Upload any file** – PDF, Word, Excel, PowerPoint, images, code, archives, and more
- **Automatic OCR** for scanned PDFs and images (requires Tesseract)
- **Intelligent summarization** – AI‑powered (transformers) or extractive fallback
- **Question answering** – ask questions about document content
- **Translation** between 15+ languages (using deep‑translator)
- **Named entity recognition** – people, organizations, locations, dates (via Stanza or regex)
- **Sentiment analysis** – positive/negative/neutral
- **Document comparison** – find similarities and differences
- **Full‑text search** across all documents
- **Asynchronous background processing** for heavy tasks
- **Export** to txt, json, md, html
- **Thumbnail generation** for images
- **Malware scanning** (basic checks)
- **MIME validation** to prevent disguised executables

## 📁 File Structure

```
iris/
├── docs/                         # Uploaded document storage
│   └── thumbnails/               # Image thumbnails
├── skills/
│   └── documentation.py          # Documentation system (this module)
└── exports/                       # Exported documents
```

## 🚀 Quick Start

1. Install required system dependencies:
   - **Tesseract OCR** (for OCR) – [Windows](https://github.com/UB-Mannheim/tesseract/wiki), macOS: `brew install tesseract`, Linux: `sudo apt install tesseract-ocr`
   - **Ollama** (optional, for local LLM fallback)

2. Python dependencies are included in `requirements.txt`. Key packages:
   - `pdfplumber`, `pytesseract`, `Pillow`, `pdf2image`, `PyPDF2`, `python-magic-bin`
   - `transformers`, `torch` (optional, for AI summarization)
   - `stanza`, `spacy` (optional, for NER)
   - `deep-translator` (optional, for translation)

3. The documentation system is automatically initialized when IRIS starts. No manual setup needed.

## 📤 Uploading Documents

You can upload documents via:
- **Drag & drop** onto the chat input area
- **Clicking the paperclip icon** in the input bar
- **Pasting** long text (over 2000 characters) – you'll be prompted to convert to a text document

Supported file types include:
- **Text**: `.txt`, `.md`, `.json`, `.csv`, `.xml`, `.html`, `.css`, `.py`, `.js`, …
- **Office**: `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.odt`, `.ods`, `.odp`
- **Images**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`, `.tiff`
- **Archives**: `.zip` (contents listed)

After upload, a system message appears with a summary and interactive options.

## 🔍 Interacting with Documents in Chat

Once a document is uploaded, you can ask questions like:
- “Summarize this document”
- “What are the key points?”
- “Extract all names”
- “Translate this to Spanish”
- “Compare with [another document]”

The AI automatically receives the document content when you use keywords like “document”, “file”, “summary”, etc.

## 📡 API Endpoints

All endpoints are under `/api/documents` and are registered by `register_documentation_routes()`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/api/documents` | List documents (with optional filters) |
| POST   | `/api/documents` | Upload a new document |
| GET    | `/api/documents/<id>` | Get document details |
| DELETE | `/api/documents/<id>` | Delete a document |
| POST   | `/api/documents/<id>/summarize` | Generate summary |
| POST   | `/api/documents/<id>/ask` | Ask a question about the document |
| GET    | `/api/documents/<id>/entities` | Extract named entities |
| GET    | `/api/documents/<id>/sentiment` | Analyze sentiment |
| POST   | `/api/documents/<id>/translate` | Translate document |
| POST   | `/api/documents/compare` | Compare two documents |
| GET    | `/api/documents/search` | Full‑text search across documents |
| POST   | `/api/documents/<id>/export` | Export document (txt, json, md, html) |
| GET    | `/api/documents/stats` | Get document statistics |
| GET    | `/exports/<filename>` | Serve exported files |
| GET    | `/docs/thumbnails/<filename>` | Serve image thumbnails |

## ⚙️ Configuration

The documentation system uses its own SQLite database (`iris_docs.db`) and stores files in the `docs/` directory. You can adjust the following in `documentation.py`:

- `chunk_size` (default 1000) – size of text chunks for RAG
- `chunk_overlap` (default 200) – overlap between chunks
- `max_file_size` (default 100 MB)

## 🧠 AI Processing Pipeline

1. **File validation** – extension, MIME type, malware scan
2. **Content extraction** – depending on file type (PDF, Office, image, etc.)
3. **OCR** – if image or scanned PDF, Tesseract extracts text
4. **Chunking** – text split into overlapping chunks with keyword extraction
5. **Summarization** – AI model (if available) or extractive method
6. **Thumbnail generation** – for images
7. **Database storage** – document metadata and chunks saved
8. **Background processing** – entities, sentiment, language detected asynchronously

## 🐛 Troubleshooting

### Upload fails with “MIME type mismatch”
Add the detected MIME type to `MIME_TYPES` in `documentation.py`. For example:
```python
'application/CDFV2': ['ppt'],
```

### OCR not working
Ensure Tesseract is installed and the path is correctly set in `documentation.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```
Test with `tesseract --version`.

### “Documentation system failed to load” on startup
Check the full traceback – usually a missing dependency. Ensure all required packages are installed (see `requirements.txt`). On Python 3.14, spaCy may fail; you can safely remove it – the system falls back to stanza and regex.

## 📄 License

MIT License – see the main [LICENSE](LICENSE) file.
```