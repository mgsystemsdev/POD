FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (layer cache)
COPY system/dashboard/requirements.txt ./dashboard/requirements.txt
RUN pip install --no-cache-dir -r dashboard/requirements.txt

# Copy application tree — preserves the relative structure that server.py's
# sys.path.insert expects: /app/services/ is one level up from /app/dashboard/
COPY system/dashboard/ ./dashboard/
COPY system/services/  ./services/
COPY system/db/        ./db/

# Log directory (overrides the home-based default in server.py)
ENV LOG_DIR=/app/logs
RUN mkdir -p /app/logs

# Railway injects PORT and DATABASE_URL automatically.
# AGENTS_API_KEY must be set as a Railway environment variable.
EXPOSE 8765

CMD ["python", "dashboard/server.py"]
