# Authentication & Authorization Report (Phase 3)

Enterprise JWT + RBAC auth was added **incrementally** without rewriting domain ML/CRUD APIs. Domain routes remain open so existing planners keep working; auth is enforced on `/api/v1/auth/*` protected endpoints and the frontend shell.

---

## Authentication Flow

1. User submits email/password → `POST /api/v1/auth/login`
2. Server validates credentials, account status, lockout, and password hash (bcrypt)
3. Server creates a `UserSession`, issues **access** + **refresh** JWTs (refresh hash stored on session)
4. Client stores tokens + user in `localStorage`
5. Axios attaches `Authorization: Bearer <access>`
6. On 401, client calls `POST /auth/refresh` (rotation), retries once, or redirects to `/login`
7. Logout revokes the current session (or all sessions)

```
Login → Session + JWT pair → Protected UI
                ↓
         Refresh rotates tokens
                ↓
         Logout revokes session
```

---

## JWT Flow

| Token | Lifetime (config) | Claims |
|-------|-------------------|--------|
| Access | `JWT_ACCESS_EXPIRE_MINUTES` (default 30) | `sub`, `type=access`, `role`, `permissions`, `sid`, `iat`, `exp` |
| Refresh | `JWT_REFRESH_EXPIRE_DAYS` (default 7) | `sub`, `type=refresh`, `role`, `permissions`, `sid`, `iat`, `exp` |

- Algorithm: HS256 (`SECRET_KEY`)
- Refresh tokens are **hashed** (SHA-256) before storage; plain JWT is returned once
- Refresh **rotates** the refresh JWT and updates `user_sessions.refresh_token_hash`
- Access tokens carry `sid` for session activity + “current session” detection

---

## RBAC Flow

1. `User.role` is an enum (`SUPER_ADMIN`, `ADMIN`, `MANAGER`, `EMPLOYEE`)
2. Enterprise `roles` / `permissions` / `role_permissions` tables are seeded for finer codes (`users.read`, `inventory.update`, …)
3. Dependencies:
   - `get_current_user` — valid access JWT + active user
   - `require_roles(*roles)`
   - `require_permission(code)`
   - `require_super_admin`
4. Frontend: `ProtectedRoute`, `PermissionGuard`, role-filtered sidebar via `canAccessPath`

### Permission matrix (seeded examples)

| Role | Typical permissions |
|------|---------------------|
| SUPER_ADMIN | All seeded codes |
| MANAGER / ADMIN | Forecast, staff, inventory, feedback, settings |
| INVENTORY_MANAGER | `inventory.*` |
| CASHIER | `orders.*` |
| EMPLOYEE | Limited UI routes (dashboard, forecast, staff, inventory, profile, sessions) |

User-facing role enum on `users.role` remains the API source of truth for JWT `role`.

---

## API Documentation

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/login` | No | Login; returns user + tokens |
| POST | `/api/v1/auth/refresh` | No (refresh body) | Rotate tokens |
| POST | `/api/v1/auth/logout` | Yes | Revoke session(s) |
| GET | `/api/v1/auth/me` | Yes | Current user |
| POST | `/api/v1/auth/change-password` | Yes | Change password + history |
| POST | `/api/v1/auth/forgot-password` | No | Issues reset token (dev returns token in body) |
| POST | `/api/v1/auth/reset-password` | No | Consume reset token |
| GET | `/api/v1/auth/sessions` | Yes | List active sessions (`is_current`) |
| POST | `/api/v1/auth/sessions/revoke-others` | Yes | Force-logout other devices |
| DELETE | `/api/v1/auth/sessions/{id}` | Yes | Terminate one session |

Envelope:

```json
{ "success": true, "message": "...", "data": { } }
```

Errors use the global handlers (`401`, `403`, `404`, `422`) with the same shape.

### Demo credentials (seed)

- `admin@restaurant.com` / `Admin@12345` (ADMIN)
- `manager@restaurant.com` / `Admin@12345`
- `superadmin@restaurant.com` / `Admin@12345`

---

## Password & account security

- bcrypt hashing (`passlib`); never store plaintext
- Strength: min length, upper, lower, digit, special
- Password history (last 5) on change/reset
- Failed login counter + lockout (`MAX_FAILED_LOGIN_ATTEMPTS`, `ACCOUNT_LOCK_MINUTES`)
- Fields ready: `email_verified`, `password_changed_at` (expiration policy hook)
- Email verification tokens table ready for future mail delivery

---

## Session management

`user_sessions` tracks login metadata: IP, user-agent, device, OS, browser, last activity, refresh hash, revoke/logout timestamps. Multiple concurrent sessions supported; force logout via revoke endpoints.

---

## Middleware & security posture

| Layer | Status |
|-------|--------|
| CORS | Configured (`CORS_ORIGINS`) |
| Security headers | `SecurityHeadersMiddleware` |
| Request logging | `RequestLoggingMiddleware` |
| Auth context | `AuthenticationMiddleware` (non-blocking; DI enforces) |
| Rate limiting | Ready (`RATE_LIMIT_ENABLED=false` by default) |
| CSRF / token blacklist | Hooks / ready for later enablement |
| Refresh rotation | Implemented |

Domain ML routes are **not** JWT-gated yet (intentional compatibility). Gate sensitive ops (retrain, regenerate) in a follow-up using `require_roles` / `require_permission`.

---

## Database changes

Migration: `298a40641d4f_auth_sessions_tokens_user_security.py`

| Table / columns | Purpose |
|-----------------|---------|
| `user_sessions` | Multi-device sessions + refresh hash |
| `password_reset_tokens` | Forgot/reset flow |
| `email_verification_tokens` | Verification-ready |
| `password_history` | Reuse prevention |
| `users.email_verified`, `failed_login_attempts`, `locked_until`, `last_login_at`, `password_changed_at` | Account security |
| Existing `roles`, `permissions`, `role_permissions`, `audit_logs` | RBAC + audit |

Audit events: login (success/fail), logout, password change/reset.

---

## Frontend

| Route | Purpose |
|-------|---------|
| `/login` | Sign in |
| `/forgot-password` | Request reset (shows dev token) |
| `/reset-password` | Apply reset token |
| `/profile` | Profile + change password |
| `/sessions` | Active sessions / terminate |
| `/unauthorized` | 403 page |
| App shell | Wrapped in `ProtectedRoute` + `AuthProvider` |

Also: Axios 401→refresh retry, role-based sidebar, navbar user + logout, `PermissionGuard` for section-level checks.

---

## Files added

**Backend**

- `app/models/auth.py`
- `app/schemas/auth.py`
- `app/services/auth_service.py`
- `app/api/auth.py`
- `app/middleware/auth_middleware.py`
- `migrations/versions/298a40641d4f_auth_sessions_tokens_user_security.py`

**Frontend**

- `src/store/index.js`
- `src/services/authService.js`
- `src/context/AuthContext.jsx`
- `src/components/auth/ProtectedRoute.jsx`
- `src/components/auth/PermissionGuard.jsx`
- `src/pages/Login.jsx`, `ForgotPassword.jsx`, `ResetPassword.jsx`, `Profile.jsx`, `Sessions.jsx`, `Unauthorized.jsx`

**Docs**

- `docs/AUTHENTICATION_REPORT.md` (this file)

---

## Files modified (high level)

- `app/api/v1/router.py` — mount auth router
- `app/api/dependencies.py` — JWT + RBAC deps
- `app/models/user.py` — security columns
- `app/db/seed.py` — bcrypt demo users + RBAC seed
- `app/main.py` — auth middleware
- `app/core/config.py` — JWT / lockout settings
- Frontend `App.jsx`, `main.jsx`, `api/client.js`, `Navbar.jsx`, `Sidebar.jsx`

---

## Verification performed

- Login / me / refresh / sessions / forgot / logout → HTTP 200
- OpenAPI lists `/api/v1/auth/*`
- `/forecast/latest` still reachable without JWT (compatibility)

### How to run

```powershell
# Backend
cd Backend
.\venv\Scripts\Activate.ps1
python run.py   # port from .env (8001)

# Frontend
cd Frontend
npm run dev     # http://localhost:5173
```

Sign in with `admin@restaurant.com` / `Admin@12345`.

---

## Recommended next steps

1. Enforce JWT on sensitive mutations (`/forecast/retrain`, `/dataset/regenerate`, settings writes)
2. Wire real email delivery for forgot-password / verification (stop returning raw tokens in production)
3. Enable rate limiting on `/auth/login` and `/auth/forgot-password`
4. Optional CSRF cookie mode for browser-only clients
