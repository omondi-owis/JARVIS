# J.A.R.V.I.S. Production Dockerfile
FROM python:3.11-slim

LABEL owner="Raphael" \
      name="J.A.R.V.I.S." \
      description="Private Remote Voice AI & Operations System"

# Security hardening
RUN useradd -r -s /bin/false -d /app jarvis && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
        sudo \
        ufw \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# Copy application
COPY . .

# Create necessary directories with correct perms
RUN mkdir -p logs config && \
    touch logs/.gitkeep logs/audit.jsonl && \
    chown -R jarvis:jarvis /app && \
    chmod 700 config && \
    chmod 600 logs/audit.jsonl || true

# Never run as root
USER jarvis

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Least privilege - use uvicorn directly, not gunicorn as root
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
