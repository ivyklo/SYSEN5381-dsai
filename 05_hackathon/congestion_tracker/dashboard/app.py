# app.py
# City Congestion Tracker – Shiny for Python app
# Pairs with WALKTHROUGH.md and README.md
# This wraps the UI and server modules into a runnable Shiny app.

from shiny import App
import os

from ui import app_ui
from server import server

app = App(app_ui, server)

if __name__ == "__main__":
    # Run with: python app.py
    # Locally this will default to http://127.0.0.1:8002
    # On platforms like DigitalOcean, use the PORT env var and 0.0.0.0.
    from shiny import run_app

    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")
    run_app(app, host=host, port=port)

