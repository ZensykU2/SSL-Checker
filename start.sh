#!/bin/bash
echo "Warte auf Datenbank..."
sleep 5  

echo "Lade Umgebungsvariablen..."
export $(grep -v '^#' .env | xargs)

echo "Migrationen werden ausgeführt..."
alembic -c /app/alembic.ini upgrade head

echo "Starte FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
