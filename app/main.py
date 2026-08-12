from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.services.agent_service import process_message

schema = """
Table: sales
Columns:
    id INTEGER
    country TEXT
    product TEXT
    quantity INTEGER
    unit_price REAL
    total_amount REAL
    sale_date DATE
"""

BASE_DIR = Path(__file__).resolve().parents[1]
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=FileResponse)
async def root() -> Path:
    return STATIC_DIR / "index.html"


class ChatRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)


def _cleanup_result_key(key: str) -> str:
    normalized = key.strip().lower().replace("_", " ")
    normalized = normalized.replace("sum(", "").replace("count(", "").replace("avg(", "").replace("average(", "").replace("min(", "").replace("max(", "").replace(")", "").strip()

    if "total amount" in normalized or "total sales" in normalized:
        return "Total sales amount"
    if "quantity" in normalized:
        return "Quantity"
    if "average" in normalized or "avg" in normalized:
        return "Average"
    if "count" in normalized:
        return "Count"
    if normalized:
        return normalized.capitalize()
    return "Result"


def _format_query_message(result: object) -> str:
    if isinstance(result, list):
        if not result:
            return "The query returned no rows."

        first_row = result[0]
        if isinstance(first_row, dict) and len(result) == 1 and len(first_row) == 1:
            key, value = next(iter(first_row.items()))
            label = _cleanup_result_key(key)
            return f"{label}: {value}"

        return f"Query returned {len(result)} row(s)."

    if isinstance(result, dict):
        if len(result) == 1:
            key, value = next(iter(result.items()))
            label = _cleanup_result_key(key)
            return f"{label}: {value}"
        return "Query returned a result."

    return f"Query result: {result}"


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: ChatRequest) -> dict[str, object]:
    try:
        response = await asyncio.to_thread(
            process_message,
            request.message,
            request.session_id,
            schema,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception:
        raise HTTPException(status_code=500, detail="Internal server error")

    if response.get("type") == "email":
        return {"success": True, "message": "Summary sent successfully."}

    if response.get("type") == "query":
        message = _format_query_message(response.get("result"))
        return {"success": True, "message": message}

    return {"success": True, "message": "Request completed successfully."}
