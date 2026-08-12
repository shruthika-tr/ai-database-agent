from __future__ import annotations

from typing import Any

from sqlalchemy import text

from app.database import engine
from app.services.sql_service import validate_select_sql


def execute_sql(sql: str) -> list[dict[str, Any]]:
    """Validate and execute a safe SELECT statement against the SQLite database."""
    validate_select_sql(sql)

    with engine.connect() as connection:
        result = connection.execute(text(sql))
        rows = result.mappings().all()

    return [dict(row) for row in rows]
