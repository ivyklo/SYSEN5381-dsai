# Codebook — City Congestion Tracker

## Data files

| File | Description |
|------|--------------|
| `data/locations.csv` | One row per monitored location (intersection/segment/zone). |
| `data/congestion_readings.csv` | One row per congestion reading across **Test A/B/C**: location, timestamp, level, delay, dataset label. |

## locations.csv

| Variable | Type | Description |
|----------|------|-------------|
| `location_id` | character | Unique id (e.g. `downtown_1`). |
| `name` | character | Human-readable name (e.g. "Main & 5th"). |
| `zone` | character | Area/zone (e.g. downtown, highway, bridge). |

## congestion_readings.csv

| Variable | Type | Description |
|----------|------|-------------|
| `location_id` | character | References `locations.location_id`. |
| `ts` | datetime (ISO8601) | Time of the reading. |
| `congestion_level` | integer | 1 = low, 2 = moderate, 3 = high, 4 = severe. |
| `delay_minutes` | numeric | Estimated delay in minutes (derived from level + noise). |
| `dataset_label` | character | Test dataset identifier: `dataset_a` (last 30 days), `dataset_b` (last 14 days), `dataset_c` (last 7 days). |

## Database schema (Supabase)

- **locations**: `location_id` (PK), `name`, `zone`, `created_at`.
- **congestion_readings**: `id` (PK), `location_id` (FK), `ts`, `congestion_level`, `delay_minutes`, `dataset_label`, `created_at`.

Synthetic data is generated with 7 locations and 15-minute readings across three test datasets:
- **Test A**: last 30 days (`dataset_a`)
- **Test B**: last 14 days (`dataset_b`)
- **Test C**: last 7 days (`dataset_c`)

Congestion is higher during rush hours (7–9, 16–18).
