# generate_synthetic_data.py
# Generate Synthetic Congestion Data (Python)
# Pairs with supabase/schema.sql, README.md, and WALKTHROUGH.md
#
# This script:
# - Creates 3 labeled test datasets (Dataset A, B, C) with different seeds and time ranges
# - Writes CSVs to ../data/ per dataset
# - Optionally loads all datasets into Supabase PostgreSQL using psycopg2
#
# Students learn how to:
# - Use pandas and numpy to generate synthetic time series data
# - Load environment variables from a shared .env
# - Connect to Supabase (Postgres) from Python

# 0. Setup #################################

## 0.1 Load packages ############################

import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv


## 0.2 Environment ###############################

# Load .env from repo root (SYSEN5381-dsai, the folder that contains 05_hackathon)
ROOT_DIR = Path(__file__).resolve().parents[3]
PROJECT_DIR = Path(__file__).resolve().parents[1]
_env_loaded = False
for env_path in [ROOT_DIR / ".env", PROJECT_DIR / ".env"]:
    if env_path.exists():
        load_dotenv(env_path)
        _env_loaded = True
        print(f"Loaded .env from {env_path}")
        break
if not _env_loaded:
    print(
        f".env not found at {ROOT_DIR / '.env'} or {PROJECT_DIR / '.env'}. "
        "Put .env in SYSEN5381-dsai (repo root) with SUPABASE_DB_* to push to Supabase."
    )


# 1. Generate locations (shared across all datasets) ##########

locations = pd.DataFrame(
    {
        "location_id": [
            "downtown_1",
            "downtown_2",
            "highway_e",
            "highway_w",
            "bridge_n",
            "bridge_s",
            "airport_rd",
        ],
        "name": [
            "Main & 5th",
            "Center & State",
            "Highway 9 East",
            "Highway 9 West",
            "North Bridge",
            "South Bridge",
            "Airport Rd",
        ],
        "zone": [
            "downtown",
            "downtown",
            "highway",
            "highway",
            "bridge",
            "bridge",
            "transit",
        ],
    }
)


# 2. Dataset configs: label, seed, n_days ####################

DATASET_CONFIGS = [
    {"label": "dataset_a", "name": "Dataset A", "seed": 42, "n_days": 30},
    {"label": "dataset_b", "name": "Dataset B", "seed": 123, "n_days": 14},
    {"label": "dataset_c", "name": "Dataset C", "seed": 456, "n_days": 7},
]


def generate_readings_for_dataset(locations_df: pd.DataFrame, label: str, seed: int, n_days: int) -> pd.DataFrame:
    """Generate congestion readings for one test dataset."""
    interval_mins = 15
    n_per_day = int(24 * 60 / interval_mins)
    n_readings_per_location = n_days * n_per_day

    np.random.seed(seed)
    now = datetime.utcnow()
    base_ts = now - timedelta(days=n_days)

    records = []
    for _, loc in locations_df.iterrows():
        for i in range(n_readings_per_location):
            ts = base_ts + timedelta(minutes=i * interval_mins)
            hour = ts.hour + ts.minute / 60.0
            rush = 1 if (7 <= hour <= 9) or (16 <= hour <= 18) else 0
            level_raw = 1 + rush * 1.5 + np.random.normal(0, 0.6)
            congestion_level = int(np.clip(round(level_raw), 1, 4))
            delay_minutes = round(congestion_level * (2 + np.random.uniform(0, 3)), 2)
            records.append(
                {
                    "location_id": loc["location_id"],
                    "ts": ts.isoformat(),
                    "congestion_level": congestion_level,
                    "delay_minutes": delay_minutes,
                    "dataset_label": label,
                }
            )
    return pd.DataFrame.from_records(records)


# 3. Generate all 3 datasets and write one combined CSV ########

data_dir = Path(__file__).resolve().parents[1] / "data"
data_dir.mkdir(parents=True, exist_ok=True)

# Shared locations (no dataset_label)
locations_path = data_dir / "locations.csv"
locations.to_csv(locations_path, index=False)
print(f"Wrote {locations_path}")

all_readings = []
for cfg in DATASET_CONFIGS:
    df = generate_readings_for_dataset(
        locations,
        label=cfg["label"],
        seed=cfg["seed"],
        n_days=cfg["n_days"],
    )
    all_readings.append(df)
    print(f"Generated {cfg['name']}: {cfg['n_days']} days, seed {cfg['seed']}")

# Single CSV with all 3 datasets (dataset_label column identifies A, B, C)
readings_combined = pd.concat(all_readings, ignore_index=True)
readings_path = data_dir / "congestion_readings.csv"
readings_combined.to_csv(readings_path, index=False)
print(f"Wrote {readings_path} (Datasets A, B, C combined; {len(readings_combined)} rows)")


# 4. Optional: load into Supabase #############################

db_host = os.getenv("SUPABASE_DB_HOST")
db_name = os.getenv("SUPABASE_DB_NAME", "postgres")
db_user = os.getenv("SUPABASE_DB_USER")
db_pass = os.getenv("SUPABASE_DB_PASSWORD")
db_port = int(os.getenv("SUPABASE_DB_PORT", "5432"))

missing = [k for k, v in [("SUPABASE_DB_HOST", db_host), ("SUPABASE_DB_USER", db_user), ("SUPABASE_DB_PASSWORD", db_pass)] if not v]
if missing:
    print(
        "Supabase credentials not set (missing: " + ", ".join(missing) + "). "
        "CSV files written; set these in .env and re-run to push to Supabase."
    )
else:
    try:
        conn = psycopg2.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_pass,
            sslmode="require",
        )
        try:
            with conn.cursor() as cur:
                # Ensure dataset_label column exists (for existing DBs created before this feature)
                cur.execute(
                    "ALTER TABLE congestion_readings ADD COLUMN IF NOT EXISTS dataset_label TEXT DEFAULT 'default'"
                )
                cur.execute(
                    "CREATE INDEX IF NOT EXISTS idx_readings_dataset ON congestion_readings(dataset_label)"
                )
                cur.execute("TRUNCATE congestion_readings CASCADE")
                cur.execute("DELETE FROM locations")
                for _, row in locations.iterrows():
                    cur.execute(
                        """
                        INSERT INTO locations (location_id, name, zone)
                        VALUES (%s, %s, %s)
                        """,
                        (row["location_id"], row["name"], row["zone"]),
                    )
                for df in all_readings:
                    reading_rows = list(
                        df[["location_id", "ts", "congestion_level", "delay_minutes", "dataset_label"]].itertuples(
                            index=False, name=None
                        )
                    )
                    cur.executemany(
                        """
                        INSERT INTO congestion_readings (location_id, ts, congestion_level, delay_minutes, dataset_label)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        reading_rows,
                    )
            conn.commit()
            print("Loaded locations and all 3 test datasets (dataset_a, dataset_b, dataset_c) into Supabase.")
        finally:
            conn.close()
    except Exception as e:
        print(f"Failed to push to Supabase: {e}")
        raise
