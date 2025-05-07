#!/bin/bash

MESSAGE=$1
APPLY=$2

if [ -z "$MESSAGE" ]; then
  echo "Please provide a migration message."
  echo "To use: ./migrate.sh \"Your migration message\" [--apply|-a]"
  exit 1
fi

docker compose exec web alembic revision --autogenerate -m "$MESSAGE"

if [ "$APPLY" == "--apply" ] || [ "$APPLY" == "-a" ]; then
  echo "Applying migration..."
  docker compose exec web alembic upgrade head
else
  echo "Migration created. Not applied. Use '--apply' or '-a' to apply it."
fi
