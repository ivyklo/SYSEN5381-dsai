# utils.py
# Helper functions for OpenAQ API queries
# Pairs with project_design_for_ai_product_for_hw1.md
# Tim Fraser
#
# This module handles API calls, data cleanup, and summary statistics.
# Uses OpenAQ v3 API; date fields are nested under period.datetimeFrom/datetimeTo.

from __future__ import annotations

from datetime import datetime, date
import os
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv

# 0. Setup ####################################################################

_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_root / ".env")

BASE_URL = "https://api.openaq.org/v3"

# 1. API Key and Date Helpers #################################################


def resolve_api_key(override_key: str | None) -> str:
    """Return the API key from input or environment."""
    if override_key and override_key.strip():
        return override_key.strip()
    api_key = os.getenv("X-API-Key")
    if not api_key:
        raise ValueError("Missing API key. Set X-API-Key in .env or enter it in the app.")
    return api_key


def format_date_start(raw_date: date | str | None) -> str:
    """Convert a date input into an ISO datetime string for the API."""
    if raw_date is None:
        raise ValueError("Start date is required.")
    if isinstance(raw_date, str):
        return f"{raw_date}T00:00:00"
    return f"{raw_date.isoformat()}T00:00:00"


def format_date_end(raw_date: date | str | None) -> str:
    """Convert a date input into an ISO datetime string for the API."""
    if raw_date is None:
        raise ValueError("End date is required.")
    if isinstance(raw_date, str):
        return f"{raw_date}T23:59:59"
    return f"{raw_date.isoformat()}T23:59:59"


# 2. API Fetch Functions ######################################################


def fetch_locations(iso_code: str, api_key: str) -> list[dict[str, Any]]:
    """Fetch monitoring locations for a given ISO code (e.g., HK)."""
    response = requests.get(
        f"{BASE_URL}/locations",
        headers={"x-api-key": api_key},
        params={"iso": iso_code},
        timeout=30,
    )
    payload = _extract_payload(response)
    return payload.get("results", [])


def fetch_monthly_averages(
    sensor_id: int,
    date_from: str,
    date_to: str,
    api_key: str,
) -> pd.DataFrame:
    """Fetch monthly PM2.5 averages for a specific sensor."""
    response = requests.get(
        f"{BASE_URL}/sensors/{sensor_id}/days/monthly",
        headers={"x-api-key": api_key},
        params={"date_from": date_from, "date_to": date_to},
        timeout=30,
    )
    payload = _extract_payload(response)
    results = payload.get("results", [])
    return _parse_monthly_results(results)


# 3. Formatting and Summaries #################################################


def build_summary(monthly_df: pd.DataFrame, threshold: float) -> str:
    """Create a short summary aligned to the project design goals."""
    if monthly_df.empty:
        return "No monthly data available to summarize."

    above = monthly_df[monthly_df["value"] >= threshold]
    above_count = above.shape[0]
    total_count = monthly_df.shape[0]
    above_pct = (above_count / total_count) * 100 if total_count else 0

    worst_months = (
        monthly_df.sort_values("value", ascending=False)
        .head(3)["month"]
        .tolist()
    )
    worst_months_text = ", ".join(worst_months) if worst_months else "No months found"

    avg_value = monthly_df["value"].mean()
    max_value = monthly_df["value"].max()

    return (
        f"Average PM2.5: {avg_value:.2f} µg/m³ | "
        f"Max PM2.5: {max_value:.2f} µg/m³\n"
        f"Months above {threshold:.0f} µg/m³: {above_count} "
        f"({above_pct:.1f}%)\n"
        f"Worst months: {worst_months_text}"
    )


def build_locations_summary(locations: list[dict[str, Any]], iso_code: str) -> str:
    """Summarize location results from the OpenAQ API."""
    if not locations:
        return f"No locations found for ISO code {iso_code}."

    names = [loc.get("name") for loc in locations if loc.get("name")]
    sample_names = ", ".join(names[:3]) if names else "No names available"
    return f"{len(locations)} locations found. Sample: {sample_names}"


# 4. Internal Helpers #########################################################


def _extract_payload(response: requests.Response) -> dict[str, Any]:
    """Validate response and return JSON payload."""
    try:
        payload = response.json()
    except ValueError as exc:
        raise ValueError("API response was not valid JSON.") from exc

    if response.status_code != 200:
        message = payload.get("message") or payload.get("error") or "Unknown API error."
        raise ValueError(f"API error {response.status_code}: {message}")
    return payload


def _parse_monthly_results(results: list[dict[str, Any]]) -> pd.DataFrame:
    """Normalize monthly results into a clean DataFrame.

    OpenAQ v3 monthly endpoint returns results with period.datetimeFrom/datetimeTo
    (not a top-level "date"), value, parameter.units, and coverage.observedCount.
    """
    rows = []
    for item in results:
        period = item.get("period") if isinstance(item.get("period"), dict) else {}
        dt_obj = (
            period.get("datetimeFrom")
            or period.get("datetimeTo")
            or item.get("datetimeFrom")
            or item.get("datetimeTo")
            or item.get("date")
        )
        date_label = _parse_month_label(dt_obj)

        param = item.get("parameter")
        unit = item.get("unit") or (param.get("units") if isinstance(param, dict) else None)

        count = item.get("count")
        if count is None and isinstance(item.get("coverage"), dict):
            count = item["coverage"].get("observedCount")

        rows.append(
            {
                "month": date_label,
                "value": item.get("value"),
                "unit": unit or "",
                "count": count,
            }
        )

    monthly_df = pd.DataFrame(rows)
    if monthly_df.empty:
        return monthly_df

    monthly_df = monthly_df.dropna(subset=["value"]).sort_values("month")
    return monthly_df


def _parse_month_label(raw_date: Any) -> str:
    """Parse the API date object into a readable month label (YYYY-MM).

    OpenAQ uses DatetimeObject: { utc: "2019-07-11T20:00:00Z", local: "..." }
    """
    if raw_date is None:
        return "Unknown"
    if isinstance(raw_date, dict):
        utc_str = raw_date.get("utc")
        local_str = raw_date.get("local")
        if utc_str:
            parsed = pd.to_datetime(utc_str, errors="coerce")
        elif local_str:
            parsed = pd.to_datetime(local_str, errors="coerce")
        elif raw_date.get("year") is not None and raw_date.get("month") is not None:
            parsed = datetime(
                int(raw_date["year"]),
                int(raw_date["month"]),
                1,
            )
        else:
            parsed = pd.NaT
    else:
        parsed = pd.to_datetime(raw_date, errors="coerce")

    if pd.isna(parsed):
        return "Unknown"
    return parsed.strftime("%Y-%m")
