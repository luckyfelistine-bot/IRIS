# IRIS v7.0 Secure - Setup Guide

## 🔒 Security Features

This secure version includes:
- ✅ Environment variable configuration (no hardcoded secrets)
- ✅ CSRF protection on all state-changing operations
- ✅ Rate limiting (200 requests/hour default)
- ✅ Input validation and sanitization
- ✅ SQL injection prevention (parameterized queries only)
- ✅ XSS protection headers and DOMPurify integration
- ✅ Secure file upload with type validation
- ✅ Comprehensive audit logging
- ✅ Dual API key support for different models

## 🚀 Quick Start

### 1. Create Project Directory

```bash
mkdir iris-secure
cd iris-secure
```

### 2. Download All Files

Download these files to your project directory:
- `app.py` → Root directory
- `.env.example` → Root directory (rename to `.env`)
- `.gitignore` → Root directory
- `requirements.txt` → Root directory
- `templates/index.html` → `templates/` folder
- `static/js/iris-app.js` → `static/js/` folder
- `static/css/iris-theme.css` → `static/css/` folder (copy from your original)

### 3. Set Up Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your actual API keys
nano .env  # or use any text editor
```

**Required in .env:**
```env
# Your NEW API key (for balanced/powerful models)
GROQ_API_KEY_PRIMARY=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

# Your OLD API key (for fast models)
GROQ_API_KEY_SECONDARY=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

# Generate a secure secret key
FLASK_SECRET_KEY=your-super-secret-random-key-here
```

### 4. Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Install optional dependencies
pip install groq edge-tts psutil pyautogui matplotlib numpy
```

### 5. Run the Application

```bash
python app.py
```

Access at: http://localhost:5000

## 🔑 API Key Configuration

### Dual Key System

| Model Type | API Key Used | Model ID |
|------------|--------------|----------|
| `fast` | SECONDARY | llama-3.1-8b-instant |
| `balanced` | PRIMARY | llama-3.3-70b-versatile |
| `powerful` | PRIMARY | llama-3.3-70b-versatile |
| `code` | PRIMARY | llama-3.3-70b-versatile |

### Why Two Keys?

- **PRIMARY (New)**: Used for high-quality responses (balanced/powerful models)
- **SECONDARY (Old)**: Used for fast/cheap responses (8B model)
- **Benefits**: Cost optimization, fallback if one key hits rate limits

## 🛡️ Security Checklist

Before deploying to production:

- [ ] Changed default `FLASK_SECRET_KEY` to random 32+ character string
- [ ] Set both `GROQ_API_KEY_PRIMARY` and `GROQ_API_KEY_SECONDARY`
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=False`
- [ ] Changed default database path from `iris_secure_v7.db`
- [ ] Enabled HTTPS (use reverse proxy like Nginx)
- [ ] Set up Redis for rate limiting (instead of memory)
- [ ] Configured firewall to block port 5000 from external access
- [ ] Set up log rotation for `logs/iris.log`
- [ ] Reviewed and customized `ALLOWED_EXTENSIONS` list

## 🔧 Production Deployment

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn (4 workers)
gunicorn -w 4 -b 127.0.0.1:5000 app:app
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 📝 Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY_PRIMARY` | None | **Required** - New API key for quality models |
| `GROQ_API_KEY_SECONDARY` | None | Optional - Old API key for fast models |
| `FLASK_SECRET_KEY` | Random | **Required** - Session encryption key |
| `FLASK_ENV` | development | Set to `production` for production |
| `FLASK_DEBUG` | False | Set to `True` only for development |
| `DATABASE_URL` | sqlite:///... | Database connection string |
| `ENABLE_CSRF` | True | Enable CSRF protection |
| `SESSION_TIMEOUT_MINUTES` | 60 | User session timeout |
| `MAX_CONTENT_LENGTH` | 52428800 | Max request size (50MB) |
| `RATELIMIT_STORAGE_URI` | memory:// | Rate limit storage (use Redis in prod) |
| `RATELIMIT_DEFAULT` | 200 per hour | Default rate limit |
| `UPLOAD_FOLDER` | uploads | File upload directory |
| `MAX_UPLOAD_SIZE` | 52428800 | Max file upload size (50MB) |
| `ALLOWED_EXTENSIONS` | txt,md,... | Allowed file types for upload |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

## 🐛 Troubleshooting

### "GROQ_API_KEY_PRIMARY not set" warning
Set your API key in the `.env` file:
```bash
echo "GROQ_API_KEY_PRIMARY=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" >> .env
```

### CSRF token errors
Make sure your browser accepts cookies and the `FLASK_SECRET_KEY` is set.

### Rate limit exceeded
The default is 200 requests/hour. Increase in `.env`:
```env
RATELIMIT_DEFAULT=1000 per hour
```

### Database errors
Delete the old database and let it recreate:
```bash
rm iris_secure_v7.db
python app.py
```

## 📚 Additional Resources

- [Flask Security Documentation](https://flask.palletsprojects.com/en/3.0.x/security/)
- [Flask-WTF Documentation](https://flask-wtf.readthedocs.io/)
- [Flask-Limiter Documentation](https://flask-limiter.readthedocs.io/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)

## 📄 License

This is a security-hardened version of IRIS v7.0. Use at your own risk.
