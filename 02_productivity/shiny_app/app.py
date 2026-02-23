# app.py
# Tung Chung PM2.5 Stats Explainer (Shiny)
# Pairs with project_design_for_ai_product_for_hw1.md
# Tim Fraser
#
# This Shiny app lets users query OpenAQ monthly PM2.5 data for Tung Chung,
# then summarizes health thresholds and worst months in a clear UI.

from shiny import App, run_app

from ui import app_ui
from server import server

app = App(app_ui, server)

if __name__ == "__main__":
    run_app(app)
