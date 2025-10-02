FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY docker/materialized_updater/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared database pool module
COPY shared /app/shared

# Copy application code
COPY docker/materialized_updater/realtime_materialized_updater.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "realtime_materialized_updater:app", "--host", "0.0.0.0", "--port", "8000"]