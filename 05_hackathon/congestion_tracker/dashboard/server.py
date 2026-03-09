# server.py
# City Congestion Tracker – Shiny for Python server logic
# Pairs with WALKTHROUGH.md and README.md
# Connects to the FastAPI backend to fetch congestion data and AI summaries.

# 0. Setup #################################

## 0.1 Load packages ############################

import os
from pathlib import Path

import httpx
import pandas as pd
from dotenv import load_dotenv
from shiny import reactive, render, ui


## 0.2 Environment ###############################

ROOT_DIR = Path(__file__).resolve().parents[3]
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    print(f"Warning: .env not found at {env_file}. Dashboard will use default API URL.")


def get_api_base() -> str:
    """Resolve the congestion API base URL."""
    return os.getenv("CONGESTION_API_URL", "http://127.0.0.1:8001")


# 1. Server function #####################################


def server(input, output, session):
    # 1.1 Reactive state #################################

    readings_df = reactive.Value(pd.DataFrame())
    summary_df = reactive.Value(pd.DataFrame())
    current_dataset = reactive.Value("dataset_a")
    ai_summary_text_val = reactive.Value(
        "Click 'Get AI summary' to request a narrative from OpenAI (for the current filters)."
    )
    api_base = get_api_base()

    # 2. Populate location checkboxes from API ###########

    @reactive.Effect
    def _load_locations():
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(f"{api_base.rstrip('/')}/locations")
                resp.raise_for_status()
                locations = resp.json()
        except Exception:
            locations = []
        choices = {"all": "All locations"}
        for loc in locations:
            lid = loc.get("location_id")
            if not lid:
                continue
            choices[lid] = loc.get("name", str(lid))
        ui.update_checkbox_group(
            "locations",
            choices=choices,
            selected=["all"],
            session=session,
        )

    # 3. Helper: current query params ####################

    def _query_params(dataset: str):
        start_date, end_date = input.date_range()
        from_ts = f"{start_date}T00:00:00Z"
        to_ts = f"{end_date}T23:59:59Z"
        params = {"from_ts": from_ts, "to_ts": to_ts, "dataset": dataset}
        locs = input.locations() or []
        if locs and "all" not in locs:
            params["location_id"] = [x for x in locs if x != "all"]
        return params

    def _fetch_readings_and_summary(dataset: str):
        base = api_base.rstrip("/")
        params = _query_params(dataset)
        try:
            with httpx.Client(timeout=20.0) as client:
                readings_resp = client.get(f"{base}/readings", params=params)
                readings_resp.raise_for_status()
                readings_json = readings_resp.json()

                summary_resp = client.get(f"{base}/summary", params=params)
                summary_resp.raise_for_status()
                summary_json = summary_resp.json()

            readings_df.set(pd.DataFrame(readings_json))
            summary_df.set(pd.DataFrame(summary_json))
            ui.notification_show("Data loaded from API.", type="message")
        except Exception as exc:
            readings_df.set(pd.DataFrame())
            summary_df.set(pd.DataFrame())
            ui.notification_show(f"Failed to load data from API: {exc}", type="error")

    def _fetch_ai_summary():
        base = api_base.rstrip("/")
        params = _query_params(current_dataset())
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.post(f"{base}/ai-summary", params=params)
                resp.raise_for_status()
                data = resp.json()
            if data.get("error"):
                ai_summary_text_val.set(f"Error: {data['error']}")
            else:
                ai_summary_text_val.set(data.get("summary") or "No summary text returned.")
            ui.notification_show("AI summary loaded from API.", type="message")
        except Exception as exc:
            ai_summary_text_val.set(f"Error requesting AI summary: {exc}")
            ui.notification_show(f"AI summary request failed: {exc}", type="error")

    # 4. Effects (load data) #############################

    @reactive.Effect
    @reactive.event(input.refresh_a)
    def _on_refresh_a():
        _fetch_readings_and_summary("dataset_a")

    @reactive.Effect
    @reactive.event(input.refresh_b)
    def _on_refresh_b():
        _fetch_readings_and_summary("dataset_b")

    @reactive.Effect
    @reactive.event(input.refresh_c)
    def _on_refresh_c():
        _fetch_readings_and_summary("dataset_c")

    @reactive.Effect
    def _initial_load():
        if readings_df().empty and summary_df().empty:
            _fetch_readings_and_summary("dataset_a")

    @reactive.Effect
    @reactive.event(input.get_summary)
    def _on_get_summary_click():
        _fetch_ai_summary()

    # 5. Outputs #########################################

    def _value_box_label():
        start_date, end_date = input.date_range()
        locs = input.locations() or []
        if "all" in locs:
            location_desc = "all locations"
        else:
            sdf = summary_df()
            if not sdf.empty and "name" in sdf.columns:
                names = sdf["name"].dropna().unique().tolist()
                location_desc = ", ".join(names) if names else "all locations"
            else:
                location_desc = "all locations"
        return f"Average congestion for {location_desc} between {start_date} and {end_date}."

    @render.ui
    def value_box():
        df = readings_df()
        if df.empty or "congestion_level" not in df.columns:
            val = "—"
        else:
            val = f"{df['congestion_level'].mean():.2f}"
        label = _value_box_label()
        return ui.card(
            {"class": "value-box-card"},
            ui.div(
                ui.div(val, class_="value-box-value"),
                ui.div(label, class_="value-box-label"),
            ),
        )

    @render.data_frame
    def readings_table():
        df = readings_df()
        if df.empty:
            df = pd.DataFrame(
                {"message": ["No readings. Click Refresh data to query the API."]}
            )
        return render.DataGrid(df.head(100))

    @render.plot
    def readings_plot():
        import matplotlib.pyplot as plt

        df = readings_df()
        if df.empty or "ts" not in df.columns:
            fig, ax = plt.subplots(facecolor="#fff")
            ax.set_facecolor("#fff")
            ax.text(0.5, 0.5, "No data to plot.", ha="center", va="center", color="#5f6368")
            ax.axis("off")
            return fig
        df = df.copy()
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
        df["date"] = df["ts"].dt.date
        if "location_name" in df.columns:
            group_cols = ["location_name", "date"]
        else:
            group_cols = ["location_id", "date"]
        grouped = (
            df.groupby(group_cols)["congestion_level"]
            .mean()
            .reset_index()
            .rename(columns={"congestion_level": "avg_level"})
        )
        fig, ax = plt.subplots(facecolor="#fff")
        ax.set_facecolor("#fff")
        for key, group in grouped.groupby(group_cols[0]):
            ax.plot(group["date"], group["avg_level"], marker="o", label=str(key))
        ax.set_xlabel("Date", color="#202124")
        ax.set_ylabel("Average congestion level", color="#202124")
        ax.set_title("Daily average congestion by location", color="#202124")
        ax.legend(facecolor="#f8f9fa", edgecolor="#dadce0", labelcolor="#202124")
        ax.tick_params(colors="#5f6368")
        for spine in ax.spines.values():
            spine.set_color("#dadce0")
        fig.autofmt_xdate()
        return fig

    @render.data_frame
    def summary_table():
        df = summary_df()
        if df.empty:
            df = pd.DataFrame(
                {"message": ["No summary data. Click Refresh data to query the API."]}
            )
            return render.DataGrid(df)
        cols = ["name", "avg_level"]
        if "name" not in df.columns and "location_id" in df.columns:
            df = df.copy()
            df["name"] = df["location_id"]
        out = df[cols].copy() if all(c in df.columns for c in cols) else df.copy()
        if "avg_level" in out.columns:
            out["avg_level"] = out["avg_level"].round(2)
        return render.DataGrid(out)

    @render.text
    def ai_summary_text():
        return ai_summary_text_val()
