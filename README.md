# Restaurant Resource Planning System (RRPS)

Machine learning-driven restaurant operations platform that forecasts customer demand, plans staff and inventory, learns from manager feedback, and continuously improves model accuracy.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Folder Structure](#folder-structure)
- [System Architecture](#system-architecture)
- [Database Schema](#database-schema)
- [Machine Learning Pipeline](#machine-learning-pipeline)
- [API Documentation](#api-documentation)
- [Installation Guide](#installation-guide)
- [Screenshots](#screenshots)
- [Future Improvements](#future-improvements)
- [License](#license)
- [Contributing](#contributing)

---

## Project Overview

RRPS is a full-stack **Self-Learning Forecaster** for restaurants. It combines machine learning predictions with operational planning (workforce, procurement, profitability) and a closed feedback loop where managers submit actual customer counts to retrain the model automatically.

The system is designed as an enterprise-style analytics dashboard with eight functional modules, PostgreSQL persistence, and versioned ML models.

---

## Features

| Module | Description |
|--------|-------------|
| **Dashboard** | Live KPIs: forecast, revenue, staff/inventory costs, model accuracy |
| **Forecast** | ML customer prediction with 15+ input features and confidence score |
| **Staff Planner** | Role-based workforce recommendations and cost breakdown |
| **Inventory Planner** | Ingredient procurement planning with safety stock |
| **Manager Feedback** | Actual vs predicted feedback triggering self-learning retraining |
| **Model Analytics** | Production model metrics, version history, training trends |
| **Prediction History** | Searchable forecast, feedback, and model history with export |
| **Settings** | Theme, API health, dataset info |

### Core capabilities

- Real-time ML forecasting (Gradient Boosting / ensemble models)
- Self-learning feedback loop with automatic model retraining
- PostgreSQL persistence for plans, predictions, and dashboard snapshots
- Model versioning (v1, v2, v3…) with production promotion
- Responsive React dashboard with dark mode
- CSV export on planner and history pages

---

## Technology Stack

| Layer | Technologies |
|-------|--------------|
| **Frontend** | React 19, Vite 8, Tailwind CSS 4, React Query, Axios, Recharts, React Router |
| **Backend** | FastAPI, SQLAlchemy, Pydantic, Uvicorn |
| **Database** | PostgreSQL |
| **ML** | scikit-learn, pandas, joblib, matplotlib |
| **Tooling** | ESLint, pytest |

---

## Folder Structure

```
Restaurant-resource-planning-system/
├── Backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   ├── database/         # DB connection, init
│   │   ├── feedback/         # Self-learning engine
│   │   ├── ml/               # Training, evaluation, pipelines
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic
│   │   └── utils/            # Config, dependencies
│   ├── dataset/              # Training CSV data
│   ├── models/               # Serialized ML artifacts (.pkl, metadata)
│   ├── tests/                # pytest suite
│   └── run.py                # API entry point
├── Frontend/
│   ├── src/
│   │   ├── components/       # UI modules (dashboard, forecast, staff, …)
│   │   ├── context/          # Theme, toast providers
│   │   ├── hooks/            # React Query hooks
│   │   ├── layouts/          # Dashboard shell
│   │   ├── pages/            # Route pages
│   │   ├── services/         # Axios API clients
│   │   └── utils/            # Formatters, form builders, chart data
│   └── .env.example
└── README.md
```

---

## System Architecture

```mermaid
flowchart TB
    subgraph Client["React Frontend (Vite)"]
        UI[Dashboard UI]
        RQ[React Query Cache]
        UI --> RQ
    end

    subgraph API["FastAPI Backend :8001"]
        ForecastAPI["/forecast/*"]
        RecAPI["/recommendation/*"]
        FeedbackAPI["/feedback/*"]
        ModelAPI["/model/*"]
        PersistAPI["/*/latest"]
    end

    subgraph Data["Data Layer"]
        PG[(PostgreSQL)]
        CSV[(Training CSV)]
        PKL[(Model Artifacts)]
    end

    subgraph ML["ML Pipeline"]
        Train[Train / Retrain]
        Predict[Predict]
        Version[Model Versioning]
    end

    RQ -->|Axios HTTP| API
    ForecastAPI --> Predict
    RecAPI --> PG
    FeedbackAPI --> Train
    FeedbackAPI --> PG
    ModelAPI --> PKL
    ModelAPI --> PG
    PersistAPI --> PG
    Train --> CSV
    Train --> PKL
    Predict --> PKL
    Version --> PG
    Version --> PKL
```

### Request flow (self-learning)

1. Manager submits forecast via **POST /forecast/predict** → prediction stored in `prediction_history`
2. System generates staff/inventory plans linked to prediction ID
3. Manager submits **POST /feedback** with actual customers
4. Feedback appends row to dataset and triggers **retraining**
5. New model version promoted to production; accuracy metrics updated

---

## Database Schema

| Table | Purpose |
|-------|---------|
| `prediction_history` | ML predictions, actuals, errors, feedback metadata |
| `staff_plan_records` | Persisted staff recommendations |
| `inventory_plan_records` | Persisted inventory plans |
| `dashboard_summaries` | Dashboard snapshot rows |
| `model_versions` | Version registry with metrics and production flag |
| `retraining_history` | Retraining audit trail |
| `accuracy_history` | Accuracy tracking over time |
| `users` | User accounts (optional auth) |

**Key relationships:** `prediction_history` → staff/inventory/dashboard records via `prediction_id`.

---

## Machine Learning Pipeline

1. **Dataset** — `Backend/dataset/restaurant_data.csv` (10k+ rows, 15+ features)
2. **Feature pipeline** — encoding, scaling via scikit-learn `Pipeline`
3. **Model selection** — RandomForest, GradientBoosting, ExtraTrees comparison
4. **Training** — best model saved with evaluation report + feature importance chart
5. **Inference** — production model serves **POST /forecast/predict**
6. **Feedback loop** — actual customers appended; model retrained on feedback
7. **Versioning** — each retrain creates `vN` artifact; previous versions archived

**Metrics tracked:** Accuracy, MAE, RMSE, R², MAPE.

---

## API Documentation

**Interactive docs:** [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

### Forecast

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/forecast/predict` | Generate customer forecast |
| GET | `/forecast/latest` | Latest saved forecast |
| GET | `/forecast/model-info` | Model metadata |

### Recommendations

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/recommendation/staff` | Staff plan |
| POST | `/recommendation/inventory` | Inventory plan |
| POST | `/recommendation/full-plan` | Full dashboard plan |
| GET | `/staff/latest` | Latest staff plan |
| GET | `/inventory/latest` | Latest inventory plan |
| GET | `/dashboard/latest` | Latest dashboard snapshot |

### Feedback & Learning

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/feedback` | Submit manager feedback (triggers retrain) |
| GET | `/feedback/history` | Prediction + feedback history |

### Model

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/model/current` | Production model metrics |
| GET | `/model/versions` | All model versions |
| GET | `/model/accuracy` | Accuracy dashboard |
| POST | `/model/retrain` | Manual retrain |

---

## Installation Guide

### Prerequisites

- Node.js 20+
- Python 3.11+
- PostgreSQL 14+

### 1. Clone repository

```bash
git clone https://github.com/your-org/Restaurant-resource-planning-system.git
cd Restaurant-resource-planning-system
```

### 2. Backend setup

```bash
cd Backend
python -m venv venv
```

**Windows:**

```powershell
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

Create `Backend/.env`:

```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/restaurant_rps
API_HOST=127.0.0.1
API_PORT=8001
```

Create database:

```sql
CREATE DATABASE restaurant_rps;
```

Start API:

```bash
python run.py
```

**Swagger UI:** [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)

### 3. Frontend setup

```bash
cd Frontend
npm install
cp .env.example .env
npm run dev
```

**App:** [http://localhost:5173](http://localhost:5173)

### 4. Production build

```bash
cd Frontend
npm run build
npm run preview
```

---

## Screenshots

> Add screenshots after deployment. Suggested captures:
>
> 1. Dashboard — KPI cards and charts
> 2. Forecast — prediction form and results
> 3. Staff Planner — role table and charts
> 4. Inventory Planner — ingredient table
> 5. Manager Feedback — submission result panel
> 6. Model Analytics — training history charts
> 7. Prediction History — tabbed history view

Store images in `docs/screenshots/` and link here.

---

## Future Improvements

- [ ] JWT authentication and role-based access (manager vs staff)
- [ ] Multi-restaurant / multi-location support
- [ ] Real-time WebSocket updates for dashboard KPIs
- [ ] Email/Slack alerts for high forecast error
- [ ] Mobile PWA with offline cache
- [ ] Kubernetes deployment with CI/CD
- [ ] Feature importance API endpoint for analytics page
- [ ] Batch forecast scheduling (cron-based)
- [ ] Integration with POS systems for automatic actuals

---

## License

MIT (or your chosen license)

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

**Restaurant Resource Planning System** — Built with FastAPI, React, and scikit-learn.
