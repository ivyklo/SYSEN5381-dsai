# app.py
# City Congestion Tracker – Shiny for Python app
# Pairs with WALKTHROUGH.md and README.md
# This wraps the UI and server modules into a runnable Shiny app.

from shiny import App

from ui import app_ui
from server import server

app = App(app_ui, server)

if __name__ == "__main__":
    # Run with: python app.py
    # This will start the app on http://127.0.0.1:8002
    from shiny import run_app

    run_app(app, host="127.0.0.1", port=8002)

