-- City Congestion Tracker — Supabase PostgreSQL schema
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New query).

-- Locations: intersections, segments, or zones where we measure congestion
CREATE TABLE IF NOT EXISTS locations (
  location_id   TEXT PRIMARY KEY,
  name          TEXT NOT NULL,
  zone          TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Congestion readings: one row per location per timestamp
-- congestion_level: 1 = low, 2 = moderate, 3 = high, 4 = severe
-- dataset_label: optional test set id (e.g. 'default', 'dataset_a', 'dataset_b', 'dataset_c')
CREATE TABLE IF NOT EXISTS congestion_readings (
  id              BIGSERIAL PRIMARY KEY,
  location_id     TEXT NOT NULL REFERENCES locations(location_id) ON DELETE CASCADE,
  ts              TIMESTAMPTZ NOT NULL,
  congestion_level INTEGER NOT NULL CHECK (congestion_level BETWEEN 1 AND 4),
  delay_minutes   NUMERIC(5,2),
  dataset_label   TEXT DEFAULT 'default',
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for common filters (location, time window, dataset)
CREATE INDEX IF NOT EXISTS idx_readings_location ON congestion_readings(location_id);
CREATE INDEX IF NOT EXISTS idx_readings_ts ON congestion_readings(ts);
CREATE INDEX IF NOT EXISTS idx_readings_level ON congestion_readings(congestion_level);
CREATE INDEX IF NOT EXISTS idx_readings_dataset ON congestion_readings(dataset_label);

-- Optional: RLS (Row Level Security) — enable if you want API to use anon key
-- ALTER TABLE locations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE congestion_readings ENABLE ROW LEVEL SECURITY;
