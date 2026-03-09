-- Run this if congestion_readings already exists without dataset_label (e.g. existing Supabase project).
ALTER TABLE congestion_readings ADD COLUMN IF NOT EXISTS dataset_label TEXT DEFAULT 'default';
CREATE INDEX IF NOT EXISTS idx_readings_dataset ON congestion_readings(dataset_label);
