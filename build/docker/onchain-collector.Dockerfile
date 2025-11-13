# Multi-stage Dockerfile for Enhanced Onchain Data Collector
# Optimized for security, performance, and minimal footprint

# ================================
# Stage 1: Base Python Environment
# ================================
FROM python:3.11-slim AS python-base

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# ================================
# Stage 2: Dependencies Installation
# ================================
FROM python-base AS dependencies

# Create and use non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# ================================
# Stage 3: Application Build
# ================================
FROM dependencies AS app-build

# Copy application code
COPY --chown=appuser:appuser services/onchain-collection/ ./services/onchain-collection/
COPY --chown=appuser:appuser shared/ ./shared/
COPY --chown=appuser:appuser templates/ ./templates/

# Set permissions
RUN chown -R appuser:appuser /app && \
    chmod +x services/onchain-collection/enhanced_onchain_collector.py

# ================================
# Stage 4: Production Runtime
# ================================
FROM python:3.11-slim AS production

# Security: Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python environment from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Set working directory
WORKDIR /app

# Copy application from build stage
COPY --from=app-build --chown=appuser:appuser /app .

# Create necessary directories
RUN mkdir -p /app/logs /app/data && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app \
    SERVICE_NAME=onchain-collector \
    LOG_LEVEL=INFO

# Default command
CMD ["python", "services/onchain-collection/enhanced_onchain_collector.py"]

# ================================
# Stage 5: Development Environment
# ================================
FROM app-build AS development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov black isort mypy

# Copy test files
COPY --chown=appuser:appuser tests/ ./tests/

# Switch to non-root user
USER appuser

# Default command for development
CMD ["python", "-m", "pytest", "tests/", "-v"]