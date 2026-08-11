# BREERO API

FastAPI backend for BREERO.

## Stack

FastAPI, PostgreSQL/PostGIS, SQLAlchemy async, Psycopg 3, Alembic, Redis and Celery.

## Architecture rule

`API router -> service -> repository/query -> SQLAlchemy -> PostgreSQL`

Do not place substantial business logic in route handlers.

## Local development

From repository root:

```bash
cp .env.example .env
docker compose up --build
```

API: `http://localhost:8000`
Docs: `http://localhost:8000/docs`
Health: `http://localhost:8000/health`

## First vertical slice

1. `POST /api/v1/addresses/validate`
2. `GET /api/v1/services`
3. `GET /api/v1/services/{id}/questions`
4. `POST /api/v1/availability/search`
5. `POST /api/v1/bookings`

The current endpoints are scaffolds; domain services, repositories, persistence models, migrations and tests are the next implementation step.
