#!/bin/bash
echo "Warte auf Datenbank..."
sleep 10

echo "Migrationen werden ausgeführt..."
alembic -c /app/alembic.ini upgrade head

echo "Starte FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
