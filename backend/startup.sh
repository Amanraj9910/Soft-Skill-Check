#!/bin/bash
# Azure App Service / production startup.
# Use PORT from environment (Azure sets this).
set -e
PORT=${PORT:-8000}
exec gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app --bind "0.0.0.0:$PORT"
