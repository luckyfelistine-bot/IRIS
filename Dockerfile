# IRIS v8 — Infinite Reactive Intelligence System
FROM python:3.11-slim

LABEL maintainer="Infinite Vybeflix <aevibron@gmail.com>"
LABEL version="8.0.0"
LABEL description="IRIS - Infinite Reactive Intelligence System"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV IRIS_HOME=/app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/experiences data/iris_learnings data/iris_knowledge \
    data/iris_self data/uploads data/vector_db data/backups \
    data/sandbox data/calendar data/notes data/projects \
    static/audio

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run the application
CMD ["python", "app.py"]
