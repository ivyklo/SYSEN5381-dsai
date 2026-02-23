# server.py
# Shiny server logic for the Tung Chung PM2.5 Stats Explainer
# Pairs with project_design_for_ai_product_for_hw1.md
# Tim Fraser
#
# This module runs the API query and prepares formatted results.
# Runs query on startup and when the user clicks Run API query.

import pandas as pd
from shiny import reactive, render, ui

import utils


def server(input, output, session):
    # 0. Reactive State #######################################################

    monthly_data = reactive.Value(pd.DataFrame())
    status_message = reactive.Value("Running query on startup...")
    summary_message = reactive.Value("Loading...")
    locations_message = reactive.Value("Loading...")
    run_once = reactive.Value(False)

    # 1. Query Logic ##########################################################

    def _run_query():
        """Fetch OpenAQ data and update status, summary, and locations."""
        status_message.set("Running query...")

        try:
            api_key = utils.resolve_api_key(input.api_key())
            iso_code = "HK"
            sensor_id = int(input.sensor_id())
            start_date, end_date = input.date_range()
            date_from = utils.format_date_start(start_date)
            date_to = utils.format_date_end(end_date)
            threshold = float(input.threshold())

            locations = utils.fetch_locations(iso_code, api_key)
            monthly_df = utils.fetch_monthly_averages(
                sensor_id=sensor_id,
                date_from=date_from,
                date_to=date_to,
                api_key=api_key,
            )

            summary_text = utils.build_summary(monthly_df, threshold)
            locations_text = utils.build_locations_summary(locations, iso_code)

            monthly_data.set(monthly_df)
            summary_message.set(summary_text)
            locations_message.set(locations_text)
            status_message.set("Query completed successfully.")
            ui.notification_show("Data loaded successfully.", type="message")
        except Exception as exc:
            monthly_data.set(pd.DataFrame())
            summary_message.set("No insights available due to an error.")
            locations_message.set("No locations available due to an error.")
            status_message.set(f"Error: {exc}")
            ui.notification_show(f"Query failed: {exc}", type="error")

    # 2. Effects (Run Query) ###################################################

    @reactive.Effect
    def _run_on_startup():
        """Run query once when the app loads (uses default input values)."""
        if run_once():
            return
        run_once.set(True)
        _run_query()

    @reactive.Effect
    @reactive.event(input.run_query)
    def _on_button_click():
        """Run query when the user clicks Run API query."""
        _run_query()

    # 3. Outputs ##############################################################

    @render.data_frame
    def monthly_table():
        """Render monthly PM2.5 averages as a DataGrid (no Jinja2 dependency)."""
        df = monthly_data()
        if df.empty:
            df = pd.DataFrame(
                {"month": ["No data"], "value": [""], "unit": [""], "count": [""]}
            )
        return render.DataGrid(df)

    @render.text
    def status_text():
        return status_message()

    @render.text
    def summary_text():
        return summary_message()

    @render.text
    def locations_text():
        return locations_message()
