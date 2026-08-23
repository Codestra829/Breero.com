# BREERO Marketplace V2 Azure Target

## Timing

Azure modernization is PR-17, after the application lifecycle, security, observability and integration contracts are stable. It is not a prerequisite for Marketplace V2 and must not block the modular-monolith implementation.

## Target topology

~~~mermaid
flowchart TD
  A[Azure Front Door and WAF] --> B[Next.js applications]
  A --> C[API Management]
  C --> D[Container Apps API]
  D --> E[PostgreSQL Flexible Server]
  D --> F[Managed Redis and Service Bus]
~~~

Additional services: Blob Storage for controlled attachments, Key Vault for secrets and certificates, Application Insights and Azure Monitor for telemetry, and Defender for security posture.

## Principles

- Keep FastAPI as a modular monolith and deploy workers separately.
- PostgreSQL Flexible Server must support PostGIS and remains authoritative.
- Service Bus may replace Celery transport only through measured migration; business events remain in the database outbox.
- Blob access uses private endpoints or signed short-lived URLs with tenant authorization.
- API Management policy mirrors, but does not replace, application authorization.
- Key Vault holds secrets; workloads use managed identity where possible.
- Front Door/WAF, Container Apps and data services use private networking and explicit egress.

## Migration stages

1. Reproduce immutable application images and database migration tests.
2. Establish landing zone, identity, networking, logs and secret handling.
3. Deploy isolated staging with synthetic data.
4. Restore a verified backup to managed PostgreSQL and reconcile.
5. Run load, failure, worker-lease, outbox/inbox and security tests.
6. Perform controlled canary with rollback to the prior topology.
7. Decommission only after the observation window and backup verification.

## Exclusions

Do not introduce AKS without a documented requirement that Container Apps cannot meet. Do not replace PostgreSQL truth with search, Redis, Service Bus, Odoo or n8n. Do not combine infrastructure migration with payment activation.
