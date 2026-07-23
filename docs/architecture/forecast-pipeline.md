# Forecast Pipeline

```mermaid
flowchart TB
  subgraph inputs [Inputs]
    FE[Forecast form / BI]
    DS[Training dataset]
    FB[Manager feedback]
  end

  subgraph api [API]
    PRED[POST /forecast/predict]
    RETRAIN[POST /forecast/retrain]
    MODEL[GET /model/*]
  end

  subgraph ml [ML layer]
    PIPE[Feature pipeline]
    GBM[Gradient Boosting / ensemble]
    EVAL[Evaluation + versioning]
  end

  subgraph store [Persistence]
    PG[(PostgreSQL forecasts / snapshots)]
    ART[Joblib model artifacts]
  end

  FE --> PRED --> PIPE --> GBM --> PG
  DS --> RETRAIN --> EVAL --> ART
  FB --> RETRAIN
  MODEL --> ART
  GBM --> FE
```

## Steps

1. **Predict** — client sends restaurant context features; API loads production model; returns predicted customers/revenue band + confidence.
2. **Persist** — forecast rows and dashboard snapshots stored in PostgreSQL.
3. **Feedback** — managers submit actuals via `/feedback`; stored for learning.
4. **Retrain** — `/forecast/retrain` or `/model/retrain` rebuilds features, trains, evaluates, versions (`vN`), optionally promotes production model.
5. **Recommend** — `/recommendation/*` turns forecast into staff and inventory plans.

## Related APIs

See [API · ML & Forecast](../api/ml-forecast.md).
