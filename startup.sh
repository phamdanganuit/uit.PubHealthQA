#!/bin/bash

# Startup script for Azure App Service
set -e

echo "Starting UIT@PubHealthQA application..."

# Ensure required directories exist
mkdir -p outputs/logs
mkdir -p data/gold
mkdir -p app/static/uploads/avatars

# Set the port from Azure environment or default to 8000
export PORT=${PORT:-8000}

echo "Starting server on port $PORT"

# Run the FastAPI application using uvicorn
python -m uvicorn app:app --host 0.0.0.0 --port $PORT --workers 1