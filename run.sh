#!/bin/bash

set -e

echo "Запускаю миграции..."
alembic upgrade head

echo "Миграции успешны. Запускаю сервер..."
exec uvicorn src.app.main:app --host 0.0.0.0 --port 8000