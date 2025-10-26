# Multi-stage Dockerfile for Python Matching Engine
# Stage 1: Builder
FROM python:3.11-slim as builder

# Build arguments
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Labels
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.authors="Matching Engine Team" \
      org.opencontainers.image.url="https://github.com/your-org/matching-engine" \
      org.opencontainers.image.source="https://github.com/your-org/matching-engine" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.title="Cryptocurrency Matching Engine" \
      org.opencontainers.image.description="High-performance cryptocurrency matching engine"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Create non-root user
RUN groupadd -r matching && useradd -r -g matching matching

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --chown=matching:matching src/ ./src/
COPY --chown=matching:matching config/ ./config/

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R matching:matching /app

# Switch to non-root user
USER matching

# Expose ports
EXPOSE 8000 8765 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Default command
CMD ["python", "-m", "uvicorn", "src.matching_engine.main:app", "--host", "0.0.0.0", "--port", "8000"]
