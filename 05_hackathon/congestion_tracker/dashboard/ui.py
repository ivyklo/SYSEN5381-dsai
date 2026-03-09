# ui.py
# City Congestion Tracker – Shiny for Python UI
# Pairs with WALKTHROUGH.md and README.md
# Builds a sidebar layout to query congestion data and request an AI summary.

from shiny import ui


# 0. Constants ###########################################

APP_TITLE = "City Congestion Tracker"
APP_SUBTITLE = "Explore congestion data from Supabase and request an AI summary via OpenAI."


# 1. Sidebar Layout ######################################

sidebar = ui.sidebar(
    ui.input_date_range(
        "date_range",
        "Date range",
        start="2026-03-01",
        end="2026-03-07",
    ),
    ui.input_checkbox_group(
        "locations",
        "Locations",
        choices={"all": "All locations"},
        selected=["all"],
    ),
    ui.input_action_button("refresh_a", "Refresh Test A data", class_="btn-primary"),
    ui.input_action_button("refresh_b", "Refresh Test B data", class_="btn-primary"),
    ui.input_action_button("refresh_c", "Refresh Test C data", class_="btn-primary"),
    ui.input_action_button("get_summary", "Get AI summary", class_="btn-secondary"),
    ui.tags.p(
        "Click a Refresh Test button for Dataset A, B, or C, then Get AI summary.",
        class_="helper-text",
    ),
    width=360,
)


# 2. Custom Styles #######################################

custom_styles = ui.tags.style(
    """
    /* Light theme */
    body { background-color: #f6f7fb; color: #202124; }
    .app-title { margin-bottom: 0.25rem; color: #202124; }
    .app-subtitle { color: #5f6368; margin-top: 0; }
    .helper-text { color: #5f6368; font-size: 0.9rem; }
    .card { background-color: #fff; border: 1px solid #dadce0; box-shadow: 0 1px 3px rgba(0,0,0,0.06); color: #202124; }
    .card-header { background-color: #f8f9fa; color: #202124; font-weight: 600; border-bottom: 1px solid #dadce0; }
    .main-content { padding-bottom: 2rem; background-color: #f6f7fb; }
    hr { border-color: #dadce0; }
    .value-box-card { text-align: center; padding: 1.5rem; background-color: #fff; border: 1px solid #dadce0; color: #202124; }
    .value-box-value { font-size: 2.5rem; font-weight: 700; color: #1a73e8; }
    .value-box-label { font-size: 0.95rem; color: #5f6368; margin-top: 0.25rem; }
    .ai-summary-card { min-height: 280px; }
    .ai-summary-card pre {
        white-space: pre-wrap;
        overflow: visible;
        max-height: none;
        min-height: 200px;
        color: #202124;
    }
    .ai-summary-text { font-size: 1.25rem; min-height: 200px; }
    .ai-summary-text pre, .ai-summary-text .shiny-text-output { font-size: inherit; color: #202124; }
    .data-grid { background-color: #fff; color: #202124; }
    .data-grid table { color: #202124; }
    .data-grid th, .data-grid td { border-color: #dadce0; }
    .data-grid th { background-color: #f8f9fa; color: #202124; }
    [data-bslib-sidebar] .bslib-sidebar, .sidebar { background-color: #fff !important; color: #202124; border-right: 1px solid #dadce0 !important; }
    /* Style text inputs only; do not override checkbox/radio (breaks visibility) */
    .form-control, input:not([type=checkbox]):not([type=radio]), select, textarea { background-color: #fff !important; border-color: #dadce0 !important; color: #202124 !important; }
    label { color: #202124 !important; }
    .form-check-label { color: #202124 !important; }
    /* Keep checkboxes visible and clickable */
    .form-check { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.35rem; }
    input[type=checkbox] { width: 1.1rem; height: 1.1rem; accent-color: #1a73e8; cursor: pointer; }
    .btn-primary { background-color: #1a73e8; border-color: #1a73e8; color: #fff; }
    .btn-primary:hover { background-color: #1557b0; border-color: #1557b0; }
    .btn-secondary { background-color: #f1f3f4; border-color: #dadce0; color: #202124; }
    .btn-secondary:hover { background-color: #e8eaed; }
    """
)


# 3. Main Content Layout #################################

# Header: title + subtitle at top
header = ui.div(
    ui.tags.h1(APP_TITLE, class_="app-title"),
    ui.tags.p(APP_SUBTITLE, class_="app-subtitle"),
    ui.tags.p(
        "Test A includes the last 30 days. Test B includes the last 14 days. Test C includes the last 7 days.",
        class_="app-subtitle",
    ),
)

main_content = ui.div(
    {"class": "main-content"},
    header,
    ui.hr(),
    ui.layout_columns(
        ui.output_ui("value_box"),
        col_widths=12,
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Daily average congestion"),
            ui.output_plot("readings_plot"),
        ),
        ui.card(
            ui.card_header("Summary by location"),
            ui.output_data_frame("summary_table"),
        ),
        col_widths=(6, 6),
    ),
    ui.hr(),
    ui.layout_columns(
        ui.card(
            {"class": "ai-summary-card"},
            ui.card_header("AI summary (OpenAI)"),
            ui.div(
                ui.output_text_verbatim("ai_summary_text"),
                class_="ai-summary-text",
            ),
        ),
        col_widths=12,
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Readings (preview)"),
            ui.output_data_frame("readings_table"),
        ),
        col_widths=12,
    ),
)


# 4. Assemble App UI ####################################

app_ui = ui.page_sidebar(
    sidebar,
    custom_styles,
    main_content,
    title=APP_TITLE,
)
