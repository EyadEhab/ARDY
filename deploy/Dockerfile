# Use Python slim image for a smaller footprint
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install system dependencies needed for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies with a retry loop for unstable networks
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    for i in 1 2 3 4 5; do \
    pip install --no-cache-dir --default-timeout=1000 -r requirements.txt && break || \
    (echo "Retry $i failed, waiting 30s..." && sleep 30); \
    done

# --- Final Production Stage ---
FROM python:3.11-slim

WORKDIR /app

# Copy only the necessary libraries and binaries from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/lib/x86_64-linux-gnu /usr/lib/x86_64-linux-gnu

# Install runtime-only shared libraries and curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Security: Create a non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Environment Variables for Performance & Security
ENV TF_CPP_MIN_LOG_LEVEL=2 \
    MODEL_PATH=/app/models/crop_model.h5 \
    TREATMENTS_PATH=/app/models/treatments.json \
    PORT=8000

# Copy application code
COPY --chown=appuser:appuser app.py .

# Create models directory (to be mounted via volume in production)
RUN mkdir -p /app/models

# Expose FastAPI port
EXPOSE 8000

# Native Docker Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use Gunicorn with Uvicorn workers for production process management
# 1-2 workers are recommended for CPU-bound ML tasks to avoid OOM in small containers
# We use --timeout to allow for large model loading if needed
CMD ["gunicorn", "app:app", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
