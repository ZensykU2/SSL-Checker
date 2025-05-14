#!/bin/bash
echo "Warte auf Datenbank..."
sleep 5


echo "Migrationen werden ausgeführt..."
alembic -c /app/alembic.ini upgrade head

echo "Baue Tailwind css..."
npx @tailwindcss/cli -i ./app/static/css/input.css -o ./app/static/css/output.css

echo "Starte FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port 8000
