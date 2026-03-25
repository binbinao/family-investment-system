#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Initializing default users..."
python scripts/init_users.py || true

echo "Starting FastAPI server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
