FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    nodejs \
    npm \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Vercel CLI
RUN npm install -g vercel

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directories
RUN mkdir -p data/iris_learnings data/iris_knowledge data/iris_self data/uploads data/vector_db data/backups data/sandbox data/projects data/media

# Expose port
EXPOSE 5000

# Run
CMD ["python", "app.py"]
