# Auth API

Base path: `/api/v1/auth`

---

### POST `/api/v1/auth/login`

| Field | Value |
|-------|--------|
| **Description** | Authenticate with email/password; issue access + refresh tokens |
| **Authentication** | Public |
| **Status codes** | `200`, `401`, `423` (locked), `422`, `429` |

**Request**

```json
{
  "email": "admin@example.com",
  "password": "ChangeMe123!"
}
```

**Response `200`**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "…",
    "email": "admin@example.com",
    "full_name": "Admin",
    "roles": ["ADMIN"]
  }
}
```

**Example**

```bash
curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"ChangeMe123!"}'
```

---

### POST `/api/v1/auth/refresh`

| Field | Value |
|-------|--------|
| **Description** | Exchange refresh token for a new access token |
| **Authentication** | Public (refresh token in body) |
| **Status codes** | `200`, `401`, `422` |

**Request**

```json
{ "refresh_token": "<refresh_token>" }
```

**Response `200`**

```json
{
  "access_token": "…",
  "token_type": "bearer"
}
```

---

### POST `/api/v1/auth/logout`

| Field | Value |
|-------|--------|
| **Description** | Revoke current session |
| **Authentication** | JWT |
| **Status codes** | `200`, `401` |

**Request:** empty body (Bearer token required)

**Example**

```bash
curl -X POST "$API/auth/logout" -H "Authorization: Bearer $TOKEN"
```

---

### GET `/api/v1/auth/me`

| Field | Value |
|-------|--------|
| **Description** | Current authenticated user profile |
| **Authentication** | JWT |
| **Status codes** | `200`, `401` |

**Response `200`**

```json
{
  "id": "…",
  "email": "admin@example.com",
  "full_name": "Admin",
  "roles": ["ADMIN"],
  "is_active": true
}
```

---

### POST `/api/v1/auth/change-password`

| Field | Value |
|-------|--------|
| **Description** | Change password for the current user |
| **Authentication** | JWT |
| **Status codes** | `200`, `400`, `401`, `422` |

**Request**

```json
{
  "current_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

---

### POST `/api/v1/auth/forgot-password`

| Field | Value |
|-------|--------|
| **Description** | Request password-reset email (anti-enumeration) |
| **Authentication** | Public |
| **Status codes** | `200`, `422`, `429` |

**Request**

```json
{ "email": "user@example.com" }
```

**Response `200`**

```json
{ "message": "If the account exists, reset instructions were sent." }
```

---

### POST `/api/v1/auth/reset-password`

| Field | Value |
|-------|--------|
| **Description** | Reset password using emailed token |
| **Authentication** | Public |
| **Status codes** | `200`, `400`, `422` |

**Request**

```json
{
  "token": "<reset_token>",
  "new_password": "NewPass123!"
}
```

---

### GET `/api/v1/auth/sessions`

| Field | Value |
|-------|--------|
| **Description** | List active sessions for the current user |
| **Authentication** | JWT |
| **Status codes** | `200`, `401` |

**Response `200`**

```json
{
  "data": [
    {
      "id": "…",
      "browser": "Chrome",
      "os": "Windows",
      "ip_address": "203.0.113.10",
      "is_current": true,
      "last_activity_at": "2026-07-23T12:00:00Z"
    }
  ]
}
```

---

### POST `/api/v1/auth/sessions/revoke-others`

| Field | Value |
|-------|--------|
| **Description** | Revoke all sessions except the current one |
| **Authentication** | JWT |
| **Status codes** | `200`, `401` |

---

### DELETE `/api/v1/auth/sessions/{session_id}`

| Field | Value |
|-------|--------|
| **Description** | Revoke a specific session |
| **Authentication** | JWT |
| **Status codes** | `200`, `401`, `404` |
