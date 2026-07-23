# System Context

```mermaid
C4Context
  title RRPS System Context

  Person(manager, "Restaurant Manager", "Uses ERP, POS, forecasts")
  Person(admin, "Platform Admin", "Ops, SaaS, security")
  Person(staff, "Floor / Kitchen Staff", "POS, KDS, floor plan")

  System(rrps, "RRPS", "Restaurant ERP + ML forecasting")

  System_Ext(smtp, "Email Provider", "Password reset / notifications")
  System_Ext(obj, "Object Storage", "S3 / R2 / Azure / GCS")
  System_Ext(idp, "Optional IdP", "Future SSO")

  Rel(manager, rrps, "HTTPS")
  Rel(admin, rrps, "HTTPS")
  Rel(staff, rrps, "HTTPS")
  Rel(rrps, smtp, "SMTP / API")
  Rel(rrps, obj, "Upload / backup")
  Rel(rrps, idp, "OIDC (roadmap)")
```

## Logical layers

```mermaid
flowchart LR
  UI[Presentation<br/>React SPA]
  API[API Gateway layer<br/>FastAPI routers]
  Dom[Domain services<br/>orders, inventory, CRM…]
  Infra[Infrastructure<br/>SQLAlchemy, Redis, Celery, Storage]

  UI --> API --> Dom --> Infra
```

## Multi-tenancy (SaaS)

Organizations → restaurants → branches. Super-admin APIs under `/api/v1/saas/*` manage plans, billing, and onboarding. Tenant isolation is enforced in application services for SaaS-scoped resources.
