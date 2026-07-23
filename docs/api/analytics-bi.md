# Analytics & BI API

Authentication: **JWT**. Base: `/api/v1/bi`.

| Method | URL | Description | Auth | Status codes |
|--------|-----|-------------|------|--------------|
| GET | `/bi/executive` | Executive dashboard | JWT | 200, 401 |
| GET | `/bi/trends/revenue` | Revenue trends | JWT | 200, 401 |
| GET | `/bi/menu` | Menu analytics | JWT | 200, 401 |
| GET | `/bi/customers` | Customer analytics | JWT | 200, 401 |
| GET | `/bi/employees` | Employee analytics | JWT | 200, 401 |
| GET | `/bi/inventory/smart` | Smart inventory | JWT | 200, 401 |
| GET | `/bi/forecast/sales` | Sales forecast view | JWT | 200, 401 |
| GET | `/bi/forecast/demand` | Demand forecast view | JWT | 200, 401 |
| GET | `/bi/insights` | Insight cards | JWT | 200, 401 |
| POST | `/bi/insights/{insight_id}/acknowledge` | Ack insight | JWT | 200, 401, 404 |
| GET | `/bi/alerts` | BI alerts | JWT | 200, 401 |
| POST | `/bi/alerts/{alert_id}/resolve` | Resolve alert | JWT | 200, 401, 404 |
| POST | `/bi/assistant/query` | Natural-language assistant | JWT | 200, 400, 401 |
| GET | `/bi/reports/export` | Export report | JWT | 200, 401 |

### Example — assistant

**Request**

```json
{
  "restaurant_id": "…",
  "question": "Which menu items underperformed last week?"
}
```

**Response `200`**

```json
{
  "answer": "…",
  "citations": [],
  "suggested_actions": []
}
```

```bash
curl -X POST "$API/bi/assistant/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"restaurant_id":"…","question":"Top sellers today?"}'
```
