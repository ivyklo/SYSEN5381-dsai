# Step-by-step walkthrough: City Congestion Tracker

Follow these steps to build and run the full pipeline: **Supabase → REST API → Dashboard → AI (OpenAI)**.

---

## 1. Supabase: create project and schema

1. Go to [supabase.com](https://supabase.com) and create a new project (note the database password).
2. In the dashboard, open **SQL Editor** → **New query**.
3. Paste and run the contents of `supabase/schema.sql`. This creates `locations` and `congestion_readings` tables.
4. Under **Project Settings** → **Database**, copy the **Connection pooling** details (URI or host, port, user, password). You will need the **pooler** host (e.g. `aws-0-us-east-1.pooler.supabase.com`), not the direct connection host.

---

## 2. Synthetic data: generate and load into Supabase

1. Copy `congestion_tracker/.env.example` to the **repository root** as `.env` (same folder as `05_hackathon`, `04_deployment`, etc.).
2. In `.env`, set the Supabase DB variables:
   - `SUPABASE_DB_HOST` = pooler host (no `https://`, no port)
   - `SUPABASE_DB_PORT` = `5432`
   - `SUPABASE_DB_NAME` = `postgres`
   - `SUPABASE_DB_USER` = your pooler user (e.g. `postgres.xxxx`)
   - `SUPABASE_DB_PASSWORD` = your database password
3. From a terminal, run the Python generator:
   ```bash
   cd 05_hackathon/congestion_tracker/scripts
   python generate_synthetic_data.py
   ```
   This creates:
   - `data/locations.csv`
   - `data/congestion_readings.csv` (**Datasets A/B/C combined**) with a `dataset_label` column identifying:
     - **Test A** (`dataset_a`): last 30 days
     - **Test B** (`dataset_b`): last 14 days
     - **Test C** (`dataset_c`): last 7 days

   If `SUPABASE_DB_*` is set, it also loads the data into Supabase and ensures `congestion_readings.dataset_label` exists.

---

## 3. REST API (FastAPI, Python)

1. In `.env` (repo root), add your **OpenAI** key:
   - Get a key at [platform.openai.com](https://platform.openai.com/api-keys).
   - Set `OPENAI_API_KEY=your-key`.
2. Install Python dependencies (once) from the congestion_tracker folder:
   ```bash
   cd 05_hackathon/congestion_tracker
   pip install -r requirements.txt
   ```
3. Start the API with Uvicorn (bound to localhost only):
   ```bash
   cd 05_hackathon/congestion_tracker/api
   uvicorn fastapi_app:app --host 127.0.0.1 --port 8001
   ```
4. Check: open [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health) or run `curl http://127.0.0.1:8001/health`. Try [http://127.0.0.1:8001/locations](http://127.0.0.1:8001/locations) and `/readings`, `/summary`, `/ai-summary` (POST).

---

## 4. Dashboard (Shiny for Python)

1. Optional: in `.env` set `CONGESTION_API_URL=http://127.0.0.1:8001` (this is the default for local FastAPI).
2. With the API still running, start the dashboard (bound to localhost on port 8002):
   ```bash
   cd 05_hackathon/congestion_tracker/dashboard
   python app.py
   ```
3. In the app: open the URL shown in the console (typically [http://127.0.0.1:8002](http://127.0.0.1:8002)), pick date range and locations, then use one of:
   - **Refresh Test A data** (loads `dataset_a`)
   - **Refresh Test B data** (loads `dataset_b`)
   - **Refresh Test C data** (loads `dataset_c`)

   Click **Get AI summary** to request an OpenAI narrative for the **currently loaded test dataset + your filters**.

---

## 5. AI summary (OpenAI)

- The **API** calls OpenAI in the `POST /ai-summary` endpoint: it builds a compact summary of congestion by location from the database and sends it to OpenAI's chat completions API with a prompt asking for a short, actionable narrative (worst areas, comparison to usual, what to watch, roads to avoid).
- The **dashboard** uses the same endpoint when you click **Get AI summary**; the result is shown in the **AI summary** tab.

---

## 6. Deploy (DigitalOcean or Posit Connect)

- **API (FastAPI)**: Deploy the `api/` folder as a FastAPI service (e.g. Docker image running `uvicorn fastapi_app:app` or a Posit Connect FastAPI deployment). Configure the same environment variables (`SUPABASE_DB_*`, `OPENAI_API_KEY`) as secrets in the platform.
- **Dashboard (Shiny for Python)**: Deploy the `dashboard/` app as a Shiny for Python application, and set `CONGESTION_API_URL` in the deployment environment so it points to your deployed API URL (instead of `http://127.0.0.1:8000`).
- See `04_deployment/digitalocean/` and `04_deployment/positconnect/fastapi/` in this repo for example deployment patterns.

---

## Summary

| Step | What you do |
|------|-------------|
| 1 | Create Supabase project, run `schema.sql`. |
| 2 | Set `.env` (Supabase + later OpenAI), run `generate_synthetic_data.py` to create and load data. |
| 3 | Run FastAPI backend from `api/` with Uvicorn; test `/health`, `/locations`, `/readings`, `/summary`, `/ai-summary`. |
| 4 | Run Shiny for Python dashboard from `dashboard/`; explore data and request AI summary. |
| 5 | AI is used inside the API when `/ai-summary` is called (from dashboard or curl). |
| 6 | Deploy API and dashboard; point dashboard to deployed API URL. |
