#!/bin/sh
set -eu

if python - <<'PY'
from sqlalchemy import inspect
from app.database import engine

tables = set(inspect(engine).get_table_names())
raise SystemExit(0 if "bookshelf" in tables and "alembic_version" not in tables else 1)
PY
then
    alembic stamp head
else
    alembic upgrade head
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
