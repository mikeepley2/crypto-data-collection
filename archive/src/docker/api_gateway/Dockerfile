# Data Collection API Gateway Dockerfile
FROM python:3.10-slim

LABEL maintainer="CryptoAI Trading System"
LABEL description="Unified Data Collection API Gateway"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY src/docker/api_gateway/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/api_gateway/ ./

# Create non-root user
RUN useradd --create-home --shell /bin/bash apigateway && \
    chown -R apigateway:apigateway /app

# Create logs directory
RUN mkdir -p /app/logs && chown -R apigateway:apigateway /app/logs

# Switch to non-root user
USER apigateway

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]