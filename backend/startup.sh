#!/bin/bash
# Azure App Service / production startup.
# Use PORT from environment (Azure sets this).
set -e
PORT=${PORT:-8000}
exec gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --timeout 120 \
  --graceful-timeout 30 \
  --keep-alive 5 \
  --bind "0.0.0.0:$PORT"
