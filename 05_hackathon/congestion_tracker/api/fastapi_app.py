# fastapi_app.py
# City Congestion Tracker – FastAPI backend
# Pairs with WALKTHROUGH.md and README.md
# Converts the R Plumber API into a Python FastAPI service.
#
# This API:
# - Connects to Supabase PostgreSQL using psycopg2
# - Exposes congestion data via /locations, /readings, /summary
# - Calls Ollama Cloud via /ai-summary to generate an AI summary
#
# Students learn how to:
# - Read env vars from a shared .env
# - Query PostgreSQL from FastAPI
# - Call an external AI API (Ollama Cloud)

# 0. Setup #################################

## 0.1 Load packages ############################

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

import httpx
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel


## 0.2 Environment ###############################

# Load .env from the repo root (three levels up from this file)
ROOT_DIR = Path(__file__).resolve().parents[3]
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Safe fallback: FastAPI can still start; DB calls will fail with a clear error
    print(f"Warning: .env not found at {env_file}. Make sure it exists in the repo root.")


def get_db_conn():
    """
    Create a new PostgreSQL connection using Supabase connection pooling.
    Uses env vars: SUPABASE_DB_HOST, SUPABASE_DB_PORT, SUPABASE_DB_NAME,
    SUPABASE_DB_USER, SUPABASE_DB_PASSWORD.
    """
    host = os.getenv("SUPABASE_DB_HOST")
    user = os.getenv("SUPABASE_DB_USER")
    password = os.getenv("SUPABASE_DB_PASSWORD")
    if not host or not user or not password:
        raise HTTPException(
            status_code=500,
            detail="Database environment variables are not set. "
            "Set SUPABASE_DB_HOST, SUPABASE_DB_USER, and SUPABASE_DB_PASSWORD in .env.",
        )

    port = int(os.getenv("SUPABASE_DB_PORT", "5432"))
    dbname = os.getenv("SUPABASE_DB_NAME", "postgres")

    # Supabase requires SSL
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password,
        sslmode="require",
    )
    return conn


async def call_openai_summary(prompt_text: str) -> str:
    """
    Call OpenAI's chat completions API and return the assistant's message content.
    Uses env vars: OPENAI_API_KEY and optional OPENAI_MODEL (default: gpt-4o-mini).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set in .env.")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt_text}],
        "temperature": 0.2,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        resp.raise_for_status()
        data = resp.json()
        # Expected shape: { choices: [ { message: { role, content } } ] }
        choices = data.get("choices", [])
        if not choices:
            return str(data)
        message = choices[0].get("message", {})
        content = message.get("content")
        if not content:
            content = str(data)
        return content
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {exc}") from exc


# 1. Pydantic models #################################


class Location(BaseModel):
    location_id: str
    name: str
    zone: Optional[str] = None


class Reading(BaseModel):
    id: int
    location_id: str
    location_name: str
    ts: str
    congestion_level: int
    delay_minutes: Optional[float] = None


class SummaryItem(BaseModel):
    location_id: str
    n: int
    avg_level: float
    max_level: int
    name: Optional[str] = None
    zone: Optional[str] = None


class AISummaryResponse(BaseModel):
    summary: Optional[str]
    data: List[SummaryItem]
    error: Optional[str] = None


# 2. FastAPI app #################################

app = FastAPI(
    title="City Congestion Tracker API",
    description="REST API for congestion readings and AI summaries (FastAPI + Supabase + Ollama Cloud).",
)


# 3. Endpoints #################################


@app.get("/")
async def root():
    """
    Root endpoint (used by some deployment health checks).
    """
    return {
        "service": "City Congestion Tracker API",
        "status": "ok",
        "health": "/health",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {
        "status": "ok",
        "time": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/locations", response_model=List[Location])
async def get_locations():
    """List all locations from the locations table."""
    conn = get_db_conn()
    try:
        with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT location_id, name, zone "
                "FROM locations "
                "ORDER BY location_id"
            )
            rows = cur.fetchall()
        return [Location(**row) for row in rows]
    finally:
        conn.close()


@app.get("/readings", response_model=List[Reading])
async def get_readings(
    location_id: Optional[List[str]] = Query(
        default=None, description="Filter by location_id (can pass multiple)"
    ),
    from_ts: Optional[str] = Query(
        default=None, description="Start time (ISO8601, e.g. 2026-03-01T00:00:00Z)"
    ),
    to_ts: Optional[str] = Query(
        default=None, description="End time (ISO8601, e.g. 2026-03-07T23:59:59Z)"
    ),
    min_level: Optional[str] = Query(
        default=None, description="Minimum congestion_level (1–4)"
    ),
    level: Optional[List[int]] = Query(
        default=None, description="Filter to these congestion levels only (1–4)"
    ),
    dataset: Optional[str] = Query(
        default=None, description="Test dataset label (e.g. default, dataset_a, dataset_b, dataset_c)"
    ),
):
    """
    Get congestion readings with optional filters.
    Returns at most 1000 most recent rows for performance.
    """
    conn = get_db_conn()
    try:
        clauses = ["1=1"]
        params = []

        if location_id:
            clauses.append("r.location_id = ANY(%s)")
            params.append(location_id)
        if from_ts:
            clauses.append("r.ts >= %s")
            params.append(from_ts)
        if to_ts:
            clauses.append("r.ts <= %s")
            params.append(to_ts)
        if min_level is not None:
            try:
                min_int = int(min_level)
            except (TypeError, ValueError):
                min_int = None
            if min_int is not None:
                clauses.append("r.congestion_level >= %s")
                params.append(min_int)
        if level:
            clauses.append("r.congestion_level = ANY(%s)")
            params.append(level)
        if dataset:
            clauses.append("r.dataset_label = %s")
            params.append(dataset)

        where_sql = " AND ".join(clauses)
        sql = (
            "SELECT r.id, r.location_id, l.name AS location_name, "
            "r.ts, r.congestion_level, r.delay_minutes "
            "FROM congestion_readings r "
            "JOIN locations l ON l.location_id = r.location_id "
            f"WHERE {where_sql} "
            "ORDER BY r.ts DESC "
            "LIMIT 1000"
        )

        with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()

        # Format timestamps as ISO8601 strings
        for row in rows:
            ts_val = row.get("ts")
            if isinstance(ts_val, datetime):
                row["ts"] = ts_val.replace(tzinfo=timezone.utc).isoformat()
        return [Reading(**row) for row in rows]
    finally:
        conn.close()


@app.get("/summary", response_model=List[SummaryItem])
async def get_summary(
    from_ts: Optional[str] = Query(
        default=None, description="Start time (ISO8601). Optional."
    ),
    to_ts: Optional[str] = Query(
        default=None, description="End time (ISO8601). Optional."
    ),
    location_id: Optional[List[str]] = Query(
        default=None, description="Filter by location_id (can pass multiple)"
    ),
    level: Optional[List[int]] = Query(
        default=None, description="Filter to these congestion levels only (1–4)"
    ),
    dataset: Optional[str] = Query(
        default=None, description="Test dataset label (e.g. default, dataset_a, dataset_b, dataset_c)"
    ),
):
    """
    Per-location summary stats (count, average, max congestion_level) for an optional time window.
    """
    conn = get_db_conn()
    try:
        clauses = ["1=1"]
        params = []

        if from_ts:
            clauses.append("ts >= %s")
            params.append(from_ts)
        if to_ts:
            clauses.append("ts <= %s")
            params.append(to_ts)
        if location_id:
            clauses.append("location_id = ANY(%s)")
            params.append(location_id)
        if level:
            clauses.append("congestion_level = ANY(%s)")
            params.append(level)
        if dataset:
            clauses.append("dataset_label = %s")
            params.append(dataset)

        where_sql = " AND ".join(clauses)
        sql = (
            "SELECT location_id, "
            "COUNT(*) AS n, "
            "AVG(congestion_level) AS avg_level, "
            "MAX(congestion_level) AS max_level "
            "FROM congestion_readings "
            f"WHERE {where_sql} "
            "GROUP BY location_id "
            "ORDER BY avg_level DESC"
        )

        with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            summary_rows = cur.fetchall()

        # Join with locations to get name and zone
        with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT location_id, name, zone FROM locations")
            loc_rows = cur.fetchall()

        loc_lookup = {row["location_id"]: row for row in loc_rows}

        result = []
        for row in summary_rows:
            loc = loc_lookup.get(row["location_id"])
            row["name"] = loc.get("name") if loc else None
            row["zone"] = loc.get("zone") if loc else None
            # psycopg2 returns Decimal for avg_level; cast to float
            row["avg_level"] = float(row["avg_level"]) if row["avg_level"] is not None else 0.0
            result.append(SummaryItem(**row))

        return result
    finally:
        conn.close()


@app.post("/ai-summary", response_model=AISummaryResponse)
async def ai_summary(
    from_ts: Optional[str] = Query(
        default=None, description="Start time (ISO8601). Use with to_ts for query-based summary."
    ),
    to_ts: Optional[str] = Query(
        default=None, description="End time (ISO8601). Use with from_ts."
    ),
    days: int = Query(
        default=7, ge=1, le=30, description="If no from_ts/to_ts, summarize last N days."
    ),
    location_id: Optional[List[str]] = Query(
        default=None, description="Filter by location_id (can pass multiple)"
    ),
    level: Optional[List[int]] = Query(
        default=None, description="Filter to these congestion levels only (1–4)"
    ),
    dataset: Optional[str] = Query(
        default=None, description="Test dataset label (e.g. default, dataset_a, dataset_b, dataset_c)"
    ),
):
    """
    AI-generated narrative summary of congestion for the given filters (or last N days).
    """
    conn = get_db_conn()
    try:
        if from_ts and to_ts:
            clauses = ["ts >= %s", "ts <= %s"]
            params = [from_ts, to_ts]
            time_desc = f"from {from_ts} to {to_ts}"
        else:
            now = datetime.now(timezone.utc)
            start = now - timedelta(days=days)
            clauses = ["ts >= %s", "ts <= %s"]
            params = [start.isoformat(), now.isoformat()]
            time_desc = f"for the last {days} days"

        if location_id:
            clauses.append("location_id = ANY(%s)")
            params.append(location_id)
        if level:
            clauses.append("congestion_level = ANY(%s)")
            params.append(level)
        if dataset:
            clauses.append("dataset_label = %s")
            params.append(dataset)

        where_sql = " AND ".join(clauses)
        sql = (
            "SELECT location_id, "
            "COUNT(*) AS n, "
            "AVG(congestion_level) AS avg_level, "
            "MAX(congestion_level) AS max_level "
            "FROM congestion_readings "
            f"WHERE {where_sql} "
            "GROUP BY location_id "
            "ORDER BY avg_level DESC"
        )

        with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            summary_rows = cur.fetchall()

        if not summary_rows:
            return AISummaryResponse(
                summary=None,
                data=[],
                error="No data found for the requested time window.",
            )

        # Join with locations to add names/zones
        with conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT location_id, name, zone FROM locations")
            loc_rows = cur.fetchall()

        loc_lookup = {row["location_id"]: row for row in loc_rows}
        summary_items = []
        for row in summary_rows:
            loc = loc_lookup.get(row["location_id"])
            row["name"] = loc.get("name") if loc else None
            row["zone"] = loc.get("zone") if loc else None
            row["avg_level"] = float(row["avg_level"]) if row["avg_level"] is not None else 0.0
            summary_items.append(SummaryItem(**row))

        # Build compact text for the model
        lines = [
            f"location_id={item.location_id}, name={item.name}, zone={item.zone}, "
            f"n={item.n}, avg_level={item.avg_level:.2f}, max_level={item.max_level}"
            for item in summary_items
        ]
        table_text = "\n".join(lines)
        prompt = (
            "You are a transportation analyst. Based on this congestion data, write a short "
            "(3–5 sentence) actionable summary: which areas are worst, how it compares to "
            "typical patterns, and what to watch or which roads to avoid. Be concise.\n\n"
            f"Time window: {time_desc}\n\n"
            f"{table_text}"
        )

        summary_text = await call_openai_summary(prompt)
        return AISummaryResponse(summary=summary_text, data=summary_items, error=None)
    finally:
        conn.close()


