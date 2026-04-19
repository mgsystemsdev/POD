FROM python:3.12-slim

WORKDIR /app

# 1. Install dependencies (layer cache)
# buildContext is expected to be 'agent-system-base'
COPY system/dashboard/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copy the entire system
# This preserves:
# /app/system/dashboard/
# /app/system/services/
# /app/system/db/
COPY . .

# 3. Setup runtime environment
ENV LOG_DIR=/app/logs
RUN mkdir -p /app/logs

# Railway automatically injects PORT and DATABASE_URL
EXPOSE 8765

# 4. Run server from context root
# server.py handles its own path resolution to find services/ and index.html
CMD ["python", "system/dashboard/server.py"]
