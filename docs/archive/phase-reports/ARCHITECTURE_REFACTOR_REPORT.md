# Architecture Refactor Report

**Project:** Restaurant Resource Planning System  
**Date:** 2026-07-18  
**Approach:** Incremental, module-by-module refactor. Preserve all existing functionality.

---

## 1. Current Architecture

### Backend (FastAPI + SQLAlchemy + PostgreSQL + scikit-learn)

```
Backend/app/
├── api/           # Flat routers mounted at root (no /api/v1)
├── database/      # connection.py + init_db.py
├── dataset/       # Synthetic data generation & loading
├── feedback/      # Self-learning loop (retrain, versioning)
├── ml/            # Train / predict / artifacts
├── models/        # SQLAlchemy ORM
├── recommendation/# Rule-based staff & inventory engines
├── schemas/       # Pydantic request/response
├── services/      # Business orchestration
├── utils/         # config, exceptions, DI
└── main.py
```

**Flow:** `run.py` → `app.main:app` → lifespan (DB init, seed, train if missing) → CORS → routers.

**Two parallel domains (phased evolution):**
1. **Legacy CRUD** — `CustomerForecast` → staff/inventory/feedback tables
2. **ML Learning** — `PredictionHistory` → plan records, model versions, accuracy

**~30 endpoints** at root paths (`/forecast/predict`, `/model/retrain`, etc.). No auth.

### Frontend (Vite + React 19 + JavaScript + Tailwind v4)

```
Frontend/src/
├── components/    # feature folders + ui/ + layout/ + charts/
├── context/       # Theme, Toast
├── hooks/         # useDashboard
├── layouts/       # DashboardLayout
├── pages/         # 8 dashboard pages
├── services/      # Axios + thin API wrappers
└── utils/         # form helpers, formatters
```

**Stack note:** Runtime is **JavaScript (JSX)**, not TypeScript (despite `@types/*` leftovers).

**State:** TanStack Query + React Context. No Redux/Zustand. No auth.

---

## 2. Problems Found

### Backend
| # | Issue | Impact |
|---|--------|--------|
| 1 | No `/api/v1` versioning | Hard to evolve contracts |
| 2 | Config incomplete — ML paths, business rules hardcoded | Env drift, inflexible deploys |
| 3 | Unstructured logging (`basicConfig` only) | Poor observability |
| 4 | Error responses are `{"detail": ...}` only | Inconsistent; validation handler unregistered |
| 5 | Dual feedback/retrain paths | Confusion, desync risk |
| 6 | Dead `api/feedback.py` (unmounted) | Dead code |
| 7 | No repositories — services talk to ORM directly | Harder testing / DI |
| 8 | No Alembic migrations (`create_all` only) | Schema drift risk |
| 9 | Auth scaffolding without auth | User model unused by APIs |
| 10 | No request/response middleware logging | No audit trail |
| 11 | No security headers / rate-limit hooks | Not production-ready |
| 12 | Season/staff-ratio logic duplicated | Maintenance risk |

### Frontend
| # | Issue | Impact |
|---|--------|--------|
| 1 | No TypeScript | Weak API contracts |
| 2 | Five copy-paste ErrorCards | Duplication |
| 3 | `downloadCsv` triplicated | Duplication |
| 4 | No route lazy loading | Larger initial bundle |
| 5 | Forecast uses imperative fetch; peers use React Query | Inconsistent cache |
| 6 | Missing folders: `api/`, `store/`, `types/`, `constants/` | Target layout incomplete |
| 7 | Hardcoded restaurant name / locale | Not configurable |
| 8 | Leftover Vite template assets (`App.css`, hero.png) | Noise |
| 9 | Error interceptor strips Axios shape; some pages still read `.response` | Dead error branches |

---

## 3. Target Architecture (Incremental)

### Backend target
```
backend/app/
├── api/v1/          # Versioned routers
├── api/dependencies.py
├── api/router.py
├── core/            # config, security, logging, exceptions, constants
├── db/              # database, session, base
├── models/
├── schemas/
├── repositories/
├── services/
├── ml/
├── utils/
├── middleware/
├── tests/
└── main.py
```

### Frontend target
```
src/
├── api/ hooks/ components/ layouts/ pages/
├── contexts/ services/ store/ types/
├── utils/ constants/ assets/
```

### Compatibility strategy
- **Keep legacy root routes** while adding `/api/v1/*` (dual mount).
- **Error body** includes both new envelope (`success`, `message`, `errors`) and `detail` for frontend compatibility until the client is updated.
- **Re-export shims** from old import paths (`app.utils.config` → `app.core.config`) so existing modules keep working during migration.

---

## 4. Phased Execution Plan

| Module | Scope | Verify |
|--------|--------|--------|
| **1** | `core/` — config, logging, exceptions, security stubs, constants; middleware request logging | `/health` + existing GETs |
| **2** | `db/` — move connection/session/base; keep imports working | DB ops + predict |
| **3** | `api/v1/` dual-mount; group routers; register validation handlers | All endpoints under both prefixes |
| **4** | Repositories + thin services; remove dead code | Tests + e2e script |
| **5** | Frontend folder align + shared UI (ErrorCard, Modal, Table, Forms) | UI smoke |
| **6** | Frontend API client + lazy routes + constants | Full dashboard |
| **7** | Models indexes/constraints polish; docs update | Regression |

**Rule:** One module at a time. Verify app runs before the next.

---

## 5. Files Modified / Added (living log)

### Module 1 — Backend Core ✅ Verified 2026-07-18

**Added**
| File | Reason |
|------|--------|
| `Backend/app/core/__init__.py` | Core package exports |
| `Backend/app/core/config.py` | Strongly typed Settings (env + pool + JWT + rate limit + paths) |
| `Backend/app/core/constants.py` | Paths, API prefix, version constants |
| `Backend/app/core/logging.py` | Structured text/JSON logging helpers |
| `Backend/app/core/exceptions.py` | Exception hierarchy (+ Unauthorized/Forbidden/RateLimit) |
| `Backend/app/core/exception_handlers.py` | Consistent `{success,message,errors,detail}` handlers |
| `Backend/app/core/security.py` | JWT-ready stubs + security headers |
| `Backend/app/middleware/__init__.py` | Middleware package |
| `Backend/app/middleware/request_logging.py` | Request/response logging, security headers, rate-limit hook |
| `docs/ARCHITECTURE_REFACTOR_REPORT.md` | This report |

**Modified**
| File | Reason |
|------|--------|
| `Backend/app/main.py` | Wire logging, middleware, centralized handlers |
| `Backend/app/utils/config.py` | Re-export shim → `app.core.config` (no import breakage) |
| `Backend/app/utils/exceptions.py` | Re-export shim → `app.core.exceptions` |
| `Backend/app/utils/exception_handlers.py` | Re-export shim → `app.core.exception_handlers` |
| `Backend/.env.example` | Document new env vars |
| `Backend/.env` | Add new optional settings (kept existing DB/port) |

**Verification:** `/health`, `/forecast/latest`, `/model/current`, `/dashboard/latest` → 200; validation errors return new envelope with `detail` for frontend compat; security headers + `X-Request-ID` present.

### Module 2 — Database layer ✅ Verified 2026-07-18

**Added**
| File | Reason |
|------|--------|
| `Backend/app/db/__init__.py` | DB package exports |
| `Backend/app/db/base.py` | Declarative Base |
| `Backend/app/db/database.py` | Engine with pool settings from config |
| `Backend/app/db/session.py` | SessionLocal + `get_db` |
| `Backend/app/api/dependencies.py` | Canonical FastAPI DI entry for `get_db` |

**Modified**
| File | Reason |
|------|--------|
| `Backend/app/database/connection.py` | Re-export shim → `app.db` |
| `Backend/app/utils/dependencies.py` | Re-export shim → `app.db.session` |
| `Backend/app/database/init_db.py` | Import engine/session/Base from `app.db` |
| `Backend/app/models/*.py` | Import `Base` from `app.db.base` |
| `Backend/app/models/customer_forecast.py` | Composite index on date+hour |
| `Backend/app/models/prediction_history.py` | Composite index on date+hour |

**Verification:** App starts; health + latest snapshots + model + feedback history + dataset info → 200.

### Module 3 — API `/api/v1` ✅ Verified 2026-07-18

**Added**
| File | Reason |
|------|--------|
| `Backend/app/api/v1/__init__.py` | v1 package |
| `Backend/app/api/v1/router.py` | Aggregates all domain routers |
| `Backend/app/api/router.py` | Dual-mount: `/api/v1` + legacy root |

**Modified**
| File | Reason |
|------|--------|
| `Backend/app/api/__init__.py` | Export from `api.router` |
| `Backend/app/api/root.py` | Document versioned endpoints; remove duplicate key |

**Verification:** `/health` and `/api/v1/health` → 200; `/forecast/latest` and `/api/v1/forecast/latest` → 200 (identical payloads). Frontend unchanged (still hits legacy paths).

### Module 4 — Repositories (incremental) ✅ Verified 2026-07-18

**Added**
| File | Reason |
|------|--------|
| `Backend/app/repositories/base.py` | Generic CRUD repository |
| `Backend/app/repositories/forecast_repository.py` | Forecast data access |
| `Backend/app/repositories/prediction_repository.py` | PredictionHistory data access |
| `Backend/app/repositories/__init__.py` | Package exports |

**Modified**
| File | Reason |
|------|--------|
| `Backend/app/services/forecast_service.py` | Business layer uses ForecastRepository (pattern for remaining services) |
| `Backend/app/api/*.py` (routers) | `get_db` from `app.api.dependencies` |

**Note:** Remaining services still use ORM directly; migrate gradually using the same repository pattern. Do not rewrite ML/feedback services in one shot.

**Verification:** `/api/v1/forecast`, `/forecast`, `/api/v1/forecast/latest`, `/api/v1/health` → 200.

### Module 5 — Frontend structure + shared UI ✅ Verified 2026-07-18

**Added**
| File | Reason |
|------|--------|
| `Frontend/src/api/client.js` | Axios client with JWT-ready request interceptor + envelope-aware errors |
| `Frontend/src/api/index.js` | API package export |
| `Frontend/src/constants/config.js` | Typed app/API constants from env |
| `Frontend/src/contexts/index.js` | Alias for target `contexts/` layout |
| `Frontend/src/store/index.js` | Client store key placeholders |
| `Frontend/src/types/index.js` | JSDoc type stubs (TS migration path) |
| `Frontend/src/utils/csv.js` | Single `downloadCsv` implementation |
| `Frontend/src/components/ui/ErrorCard.jsx` | Deduplicated error card |
| `Frontend/src/components/ui/Button.jsx` | Reusable button |
| `Frontend/src/components/ui/Modal.jsx` | Reusable modal |
| `Frontend/src/components/ui/Table.jsx` | Reusable table |
| `Frontend/src/components/ui/LoadingSpinner.jsx` | Loading state |
| `Frontend/src/components/ui/ErrorPage.jsx` | Error page |
| `Frontend/.env` | Local `VITE_API_BASE_URL` → `/api/v1` |

**Modified**
| File | Reason |
|------|--------|
| `Frontend/src/App.jsx` | Route-level `React.lazy` + Suspense |
| `Frontend/src/services/api.js` | Re-export → `api/client` |
| `Frontend/src/components/*/*ErrorCard.jsx` | Thin re-exports of shared ErrorCard |
| `Frontend/src/utils/{staff,inventory,predictionHistory}.js` | Re-export shared csv helper |
| `Frontend/src/pages/Settings.jsx` | Use `APP_NAME` / `API_BASE_URL` constants |
| `Frontend/src/components/layout/Navbar.jsx` | Use `APP_NAME` |
| `Frontend/.env.example` | Document `/api/v1` base URL |

**Verification:** `npm run build` succeeds; pages split into lazy chunks.

---

## Next modules (not started)

| Module | Scope |
|--------|--------|
| 6 | Wire more pages to shared Table/Modal/Form; Forecast → React Query |
| 7 | More repositories; optional Alembic; remove dead `api/feedback.py` |
| 8 | Harden models/constraints; finalize docs |

---

## 6. Non-Goals (this refactor)

- Rewriting ML training or recommendation business rules
- Implementing full JWT auth UI (only JWT-ready backend stubs)
- Migrating frontend to TypeScript in one shot
- Removing legacy CRUD tables (preserve functionality)
- Force-pushing or rewriting git history
