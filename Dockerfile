FROM python:3.12-slim

WORKDIR /app

COPY agent-system-base/system/dashboard/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY agent-system-base/ ./

ENV LOG_DIR=/app/logs
RUN mkdir -p /app/logs

EXPOSE 8765

CMD ["python", "system/dashboard/server.py"]
