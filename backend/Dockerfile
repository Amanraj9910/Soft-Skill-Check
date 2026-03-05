# Production Dockerfile for Azure Web App for Containers / Container Apps.
# Install ffmpeg + libsndfile for audio processing.
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn
COPY . .

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "gunicorn -w 2 -k uvicorn.workers.UvicornWorker app.main:app --bind \"0.0.0.0:${PORT}\""]
