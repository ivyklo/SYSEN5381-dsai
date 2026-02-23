# ui.py
# Shiny UI for the Tung Chung PM2.5 Stats Explainer
# Pairs with project_design_for_ai_product_for_hw1.md
# Tim Fraser
#
# This module defines the user interface layout and input controls.
# Uses sidebar for inputs; main area shows status, summary, and monthly data.

from shiny import ui

# 0. Constants ###############################################################

APP_TITLE = "Tung Chung PM2.5 Stats Explainer"

# 1. Sidebar Layout ###########################################################

sidebar = ui.sidebar(
    ui.tags.h2(APP_TITLE, class_="app-title"),
    ui.tags.p(
        "Query OpenAQ monthly averages and summarize health thresholds.",
        class_="app-subtitle",
    ),
    ui.hr(),
    # Inputs
    ui.input_password(
        "api_key",
        "OpenAQ API key (optional)",
        placeholder="Uses X-API-Key from .env if blank",
    ),
    ui.tags.div(
        ui.tags.strong("Location: "),
        "HK",
        class_="mb-2",
    ),
    ui.input_numeric("sensor_id", "PM2.5 sensor ID", value=22471, min=1),
    ui.input_date_range(
        "date_range",
        "Date range",
        start="2020-01-01",
        end="2025-12-31",
        min="2020-01-01",
        max="2025-12-31",
    ),
    ui.input_numeric(
        "threshold",
        "PM2.5 health threshold (µg/m³)",
        value=35,
        min=1,
        step=1,
    ),
    ui.input_action_button("run_query", "Run API query", class_="btn-primary"),
    ui.hr(),
    ui.tags.p(
        "Tip: Adjust the date range or sensor ID, then click Run to load data.",
        class_="helper-text",
    ),
    width=360,
    class_="scrollable-sidebar",
)

# 2. Custom Styles ############################################################

custom_styles = ui.tags.style(
    """
    body { background-color: #f6f7fb; }
    .app-title { margin-bottom: 0.25rem; }
    .app-subtitle { color: #5f6368; margin-top: 0; }
    .helper-text { color: #6c757d; font-size: 0.9rem; }
    .card { box-shadow: 0 6px 16px rgba(0,0,0,0.06); border: none; }
    .card-header { background: #ffffff; font-weight: 600; }
    .main-content { padding-bottom: 2rem; }
    /* Sidebar scrollbar: ensure it works and is clickable */
    .scrollable-sidebar, .bslib-sidebar, .sidebar { overflow-y: auto !important; overflow-x: hidden !important; max-height: 100vh !important; -webkit-overflow-scrolling: touch; }
    .scrollable-sidebar::-webkit-scrollbar, .bslib-sidebar::-webkit-scrollbar, .sidebar::-webkit-scrollbar { width: 12px; }
    .scrollable-sidebar::-webkit-scrollbar-track, .bslib-sidebar::-webkit-scrollbar-track, .sidebar::-webkit-scrollbar-track { background: #f1f1f1; }
    .scrollable-sidebar::-webkit-scrollbar-thumb, .bslib-sidebar::-webkit-scrollbar-thumb, .sidebar::-webkit-scrollbar-thumb { background: #888; border-radius: 6px; }
    .scrollable-sidebar::-webkit-scrollbar-thumb:hover, .bslib-sidebar::-webkit-scrollbar-thumb:hover, .sidebar::-webkit-scrollbar-thumb:hover { background: #555; }
    """
)

# 3. Main Content Layout ######################################################

main_content = ui.div(
    {"class": "main-content"},
    ui.layout_columns(
        ui.card(
            ui.card_header("Query status"),
            ui.output_text_verbatim("status_text"),
        ),
        ui.card(
            ui.card_header("Summary insights"),
            ui.output_text_verbatim("summary_text"),
        ),
        ui.card(
            ui.card_header("Locations found"),
            ui.output_text("locations_text"),
        ),
        col_widths=(4, 4, 4),
    ),
    ui.card(
        ui.card_header("Monthly PM2.5 averages"),
        ui.output_data_frame("monthly_table"),
    ),
)

# 4. Assemble App UI ##########################################################

app_ui = ui.page_sidebar(
    sidebar,
    custom_styles,
    main_content,
)
