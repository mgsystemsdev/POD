FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY system/dashboard/requirements.txt ./dashboard/requirements.txt
RUN pip install --no-cache-dir -r dashboard/requirements.txt

# Copy application code
COPY system/dashboard/ ./dashboard/

# Expose the bundled services directory on the Python path
ENV PYTHONPATH=/app/dashboard/services

# Log and data directories
ENV LOG_DIR=/app/logs
RUN mkdir -p /app/logs /app/data

# Railway injects PORT and DATABASE_URL automatically.
# AGENTS_API_KEY must be set as a Railway environment variable.
EXPOSE 8765

CMD ["python", "dashboard/server.py"]
