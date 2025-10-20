FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r soundhash && useradd -r -g soundhash soundhash

# Copy and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories and set ownership
RUN mkdir -p /app/logs /app/temp \
    && chown -R soundhash:soundhash /app

# Switch to non-root user
USER soundhash

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "from src.database.connection import db_manager; db_manager.get_session().close()" || exit 1

# Default command (can be overridden in docker-compose.yml)
CMD ["python", "scripts/ingest_channels.py"]
