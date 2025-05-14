#!/bin/bash
echo "Warte auf Datenbank..."
sleep 5


echo "Migrationen werden ausgeführt..."
alembic -c /app/alembic.ini upgrade head

echo "Baue Tailwind css..."
cd /app
npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css

echo "Starte FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
