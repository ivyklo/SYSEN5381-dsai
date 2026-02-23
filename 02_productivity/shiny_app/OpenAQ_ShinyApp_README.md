# Tung Chung PM2.5 Stats Explainer

A Shiny for Python app that queries OpenAQ air-quality data for Tung Chung (Hong Kong), displays monthly PM2.5 averages over a user-selected date range, and summarizes health thresholds and worst months.

## 📊 Data

- **Source:** [OpenAQ API](https://docs.openaq.org/) v3
- **Content:** Monthly PM2.5 averages from sensor ID 22471 at Tung Chung Station
- **Coverage:** Monitoring locations in Hong Kong (ISO code HK) and monthly aggregates from 2020–2025

## ⚡ Quick Start

### Installation

1. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   # or: source venv/bin/activate   # macOS/Linux
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Run the app

From the project root (`dsai/`):

```bash
python -m shiny run 02_productivity/shiny_app/app.py
```

Or from inside `02_productivity/shiny_app/`:

```bash
python -m shiny run app.py
```

Then open the URL shown in the terminal (e.g. `http://127.0.0.1:8000`) in your browser.

## 📸 Screenshots

Add screenshots of the app in action (use a light theme). Create a `screenshots/` folder, save your images there, and reference them:

![App overview](screenshots/app_overview.png)

## ✨ Features and Technology

- **Features:** Query OpenAQ API on demand, date range picker, PM2.5 health threshold, summary of worst months, auto-run on startup
- **Technology:** Shiny for Python, pandas, requests, python-dotenv

## ⚙️ Configuration

### API key

The app requires an OpenAQ API key. Set it in one of two ways:

1. **In `.env` (recommended):** Create a `.env` file in the project root (`dsai/`) with:

   ```
   X-API-Key=your_openaq_api_key_here
   ```

2. **In the app:** Enter the key in the optional "OpenAQ API key" field in the sidebar. If left blank, the app uses `X-API-Key` from `.env`.

### Default values

| Setting      | Default                      | Where to change |
|-------------|------------------------------|-----------------|
| Location    | HK (fixed)                   | Not editable    |
| Sensor ID   | 22471 (Tung Chung PM2.5)     | Sidebar         |
| Date range  | 2020-01-01 to 2025-12-31     | Sidebar         |
| PM2.5 threshold | 35 µg/m³                  | Sidebar         |

## 📖 Usage Instructions

1. **Run the app** (see Quick Start). The app loads data automatically when it starts.
2. **Adjust the date range** using the date range picker in the sidebar.
3. **Change the sensor ID** if you have another sensor to query.
4. **Set the PM2.5 threshold** (default 35 µg/m³) to see how many months exceed it.
5. **Click "Run API query"** to refresh data with the new parameters.
6. **Review the results** in the Query status, Summary insights, Locations found, and Monthly PM2.5 averages cards.

## 🔌 API Reference

### OpenAQ endpoints used

| Purpose                         | Endpoint                             | Parameters                    |
|---------------------------------|--------------------------------------|-------------------------------|
| List locations in Hong Kong     | `GET /v3/locations`                  | `iso=HK`                      |
| Monthly PM2.5 averages          | `GET /v3/sensors/{id}/days/monthly`  | `date_from`, `date_to`        |

### Header

```
x-api-key: <YOUR_API_KEY>
```

### Example request

```bash
curl -H "x-api-key: YOUR_KEY" \
  "https://api.openaq.org/v3/sensors/22471/days/monthly?date_from=2023-01-01T00:00:00&date_to=2023-12-31T23:59:59"
```
