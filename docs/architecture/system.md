# BREERO System Architecture

## Architectural decision

BREERO remains a modular monolith: FastAPI, async SQLAlchemy, PostgreSQL/PostGIS, Alembic, Redis/Celery and independently deployable Next.js surfaces. Marketplace V2 extends this architecture instead of splitting premature microservices.

The complete authority is MARKETPLACE_V2.md.

## Surfaces

- breero.com — public marketplace and customer account
- partners.breero.com — provider organization and worker SaaS
- ops.breero.com — dispatch, matching and exception command center
- admin.breero.com — platform policy, trust, finance and configuration
- api.breero.com/api/v1 — compatible current API
- api.breero.com/api/v2 — additive Marketplace V2 API

Inspect actual DNS, Caddy/Kong routes and implemented OIDC callback before adding or changing hosts.

## Canonical lifecycle

Customer Intent → ProjectRequest → Qualification → Fulfillment Decision → Matching → Opportunity → LeadConnection → Conversation and Quote → Booking → Job → Verified Review.

These are separate aggregates and states. A request, match, opportunity, connection, quote or payment attempt is not a booking.

## Layering

API router → domain service/command → repository/query → async SQLAlchemy → PostgreSQL/PostGIS.

Command boundaries own commits. State, history, audit and outbox effects are one transaction. Repositories and reusable helpers add and flush only.

## Authority

| Concern | Source of truth |
|---|---|
| Identity | Keycloak at auth.codestra.co, realm codestra |
| Marketplace lifecycle | BREERO PostgreSQL |
| Geography | PostgreSQL/PostGIS |
| Ephemeral cache/queues | Redis/Celery |
| Integration routing/receipts | Codestra middleware/Kong |
| CRM projection | Odoo 19 |
| Email delivery | Klyrow/Postal |
| SMS delivery | Telnexa/Jasmin |
| Approved orchestration | n8n |
| Payment settlement | Stripe only after payment activation |

Odoo, n8n, search and Redis cannot overwrite marketplace truth.

## Identity and authorization

Humans use Authorization Code with PKCE S256. Machines use Client Credentials. Tokens are short-lived and validated for issuer, audience, expiry, tenant and permission. Server-side RBAC and provider/customer scoping are mandatory. auth.codestra.agency is deprecated and must not appear in V2 configuration.

## Reliability

Use a transactional outbox with leased delivery, FOR UPDATE SKIP LOCKED, stable event IDs, bounded retry and visible FAILED_TERMINAL. Use an idempotent integration inbox with unique provider/external-event ID. Delivery is at-least-once.

## Runtime capability

Capability configuration is authoritative in the backend and consumed by all frontends. Initial safe state keeps instant booking, automatic assignment, payments, payouts, paid leads, marketing and unrestricted communications false.

## Production safety

This planning branch contains no deployable implementation. The current request-only/manual-dispatch release remains authoritative until sequential V2 PRs pass database-backed tests, security gates, restore/rollback evidence and approved activation.

## Historical architecture

The prior architecture is retained below for context only.

# BREERO System Architecture

## Surfaces

- `breero.com` — public marketplace + customer account
- `partners.breero.com` — vendor/technician portal
- `ops.breero.com` — dispatch and operations
- `admin.breero.com` — admin and finance
- `api.breero.com/api/v1` — FastAPI backend

## Backend stack

FastAPI + PostgreSQL/PostGIS + SQLAlchemy async + Psycopg 3 + Alembic + Redis + Celery.

## Required layering

`router -> service -> repository/query -> SQLAlchemy -> PostgreSQL`

Pydantic API contracts are separate from SQLAlchemy persistence models.

## Core domains

Auth, users, customers, addresses, legal entities, service areas, services/questions, scheduling, bookings, vendors/workers, jobs, matching, dispatch, pricing, quotes, payments, earnings, payouts, notifications, audit and integrations.

## Transactional source of truth

BREERO PostgreSQL is the operational source of truth. Odoo is synchronized asynchronously through integration events/outbox processing.

## Payment truth

Stripe webhook events, after signature and idempotency verification, are authoritative for payment completion. Browser redirects are never authoritative.

## State control

Bookings and jobs use explicit domain transitions. Partner users receive command endpoints such as `/jobs/{id}/complete`, never unrestricted status patching.

## Security

Server-side RBAC/permissions, audit logging, webhook verification, idempotency, secret isolation, secure headers, CORS policy and rate limiting are required.

## Production

Backend deployment target: `49.12.145.107`.

Production topology: reverse proxy/TLS -> API -> PostgreSQL/PostGIS + Redis + workers/scheduler. Frontends remain independently deployable.
