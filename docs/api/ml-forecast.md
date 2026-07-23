# ML & Forecast API

Base: `/api/v1`.

> **Security note (v1.0):** Several forecast/ML routes are **Public** for demo/learning. Treat as a hardening item before internet exposure. Prefer JWT in production (roadmap 1.1.0).

## Forecast

| Method | URL | Description | Auth | Status codes |
|--------|-----|-------------|------|--------------|
| POST | `/forecast/predict` | Run ML prediction | Public* | 200, 400, 422 |
| GET | `/forecast/model-info` | Active model metadata | Public* | 200 |
| POST | `/forecast/retrain` | Retrain model | Public* | 200, 400 |
| GET/POST | `/forecast` | List / create forecast records | Public* | 200/201 |
| GET/PUT/DELETE | `/forecast/{forecast_id}` | CRUD item | Public* | 200, 404 |

### POST `/forecast/predict`

**Request**

```json
{
  "restaurant_type": "casual_dining",
  "day_of_week": 5,
  "is_weekend": true,
  "is_holiday": false,
  "weather": "clear",
  "temperature_c": 28,
  "marketing_spend": 5000,
  "local_events": 1
}
```

**Response `200`**

```json
{
  "predicted_customers": 186,
  "confidence": 0.82,
  "model_version": "v3",
  "features_used": ["day_of_week", "is_weekend", "…"]
}
```

```bash
curl -X POST "$API/forecast/predict" \
  -H "Content-Type: application/json" \
  -d @features.json
```

## Snapshots

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET | `/forecast/latest` | Latest forecast snapshot | Public* |
| GET | `/staff/latest` | Latest staff plan | Public* |
| GET | `/inventory/latest` | Latest inventory plan | Public* |
| GET | `/dashboard/latest` | Latest dashboard snapshot | Public* |

## Staff · Inventory planners

| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/staff` | List / create staff plans |
| GET/POST | `/inventory` | List / create inventory plans |

## Feedback learning

| Method | URL | Description |
|--------|-----|-------------|
| POST | `/feedback` | Submit actual vs predicted |
| GET | `/feedback/history` | Feedback history |
| GET/POST | `/feedback/entries` | Entry CRUD-style access |

**Feedback request**

```json
{
  "forecast_id": "…",
  "actual_customers": 172,
  "notes": "Rain reduced evening traffic"
}
```

## Dataset · Recommendations · Model

| Method | URL | Description | Auth |
|--------|-----|-------------|------|
| GET | `/dataset/info` | Dataset stats | Public* |
| POST | `/dataset/regenerate` | Regenerate synthetic data | Public* |
| POST | `/recommendation/staff` | Staff recommendation | Public* |
| POST | `/recommendation/inventory` | Inventory recommendation | Public* |
| POST | `/recommendation/full-plan` | Combined plan | Public* |
| GET | `/model/versions` | Model versions | Public* |
| GET | `/model/current` | Production model | Public* |
| GET | `/model/accuracy` | Accuracy metrics | Public* |
| POST | `/model/retrain` | Retrain + version | Public* |
