#!/bin/sh
set -e

CONFIG_FILE="${DATA_DIR}/tabula.config.json"

# Run Alembic migrations if the app is configured in multi-user mode
# (PostgreSQL). In mono mode (SQLite) tables are created by the setup wizard
# via Base.metadata.create_all().
if [ -f "$CONFIG_FILE" ]; then
    MODE=$(python -c "import json; print(json.load(open('$CONFIG_FILE'))['mode'])" 2>/dev/null || echo "unknown")
    if [ "$MODE" = "multi" ]; then
        echo "Multi-user mode detected -- running Alembic migrations..."
        alembic upgrade head
    fi
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
