# Vitaphiles — Architecture

Vitaphiles is a **modular monolith**: one FastAPI process, one React SPA, one PostgreSQL database.

```text
Browser (React + Vite)
        │  HTTPS  /api/v1  Bearer access + refresh cookie
        ▼
FastAPI (routes → services → repositories)
        │
        ├── PostgreSQL (SQLAlchemy 2 + Alembic)
        ├── Google Books / Open Library  (BookMetadataService)
        └── TMDB                         (MovieMetadataService)
```

The browser never calls TMDB or Google Books. Keys stay in backend environment variables.

---

## Classification

- **Not** microservices.
- **Not** a generic “media” microservice.
- Books and movies are **sibling domains** with shared social primitives (review, list, activity).
- Closest interview label: **layered REST monolith**.

---

## Backend layers

| Layer | Path | Responsibility |
| --- | --- | --- |
| Routes | `app/api/routes/` | HTTP, auth deps, status codes — thin |
| Schemas | `app/schemas/` | Pydantic request/response |
| Services | `app/services/` | Transactions, rules, aggregates |
| Repositories | `app/repositories/` | SQLAlchemy queries, `user_id` scoping |
| Models | `app/models/` | Tables |
| Integrations | `app/integrations/` | External HTTP clients + normalizers |
| Core | `app/core/` | Config, security, CORS, errors, rate limit |

Entry: `uvicorn app.main:app`.

---

## Frontend layers

| Layer | Path | Responsibility |
| --- | --- | --- |
| Pages | `src/pages/` | Route screens |
| Features | `src/features/` | Domain UI (books, movies, feed, …) |
| API | `src/api/` | Axios only to `/api/v1` |
| Hooks | `src/hooks/` | TanStack Query wrappers |
| Context | `src/contexts/` | Auth session |
| Layouts | `src/layouts/` | Shell, guest, mobile nav |

State: Auth Context + TanStack Query. No Redux.

---

## Auth (target; Phase 2 implements fully)

- Access JWT ~15 minutes, HS256, stored in a JS module (not localStorage).
- Refresh token hashed in DB, HttpOnly cookie, rotation + reuse detection.
- `get_current_user` on protected routes.
- Ownership: queries filtered by `user_id`; other users’ private lists → 404.

---

## External data

`BookMetadataService` and `MovieMetadataService` return **internal** Pydantic models. Provider IDs stored as `external_source` + `external_id`. Local `books` / `movies` rows are upserted on first view/track so reviews have FKs.

---

## API surface (v1)

`/api/v1/auth`, `/users`, `/books`, `/movies`, `/reviews`, `/library`, `/lists`, `/follows`, `/activity`, `/notifications`, `/recommendations`, `/search`, `/stats`.

Errors:

```json
{ "error": { "code": "RESOURCE_NOT_FOUND", "message": "Book not found" } }
```

---

## Future (documented, not built)

CDN for images, Redis for trending caches and rate limits, job queue for recs and email, read replicas, OpenSearch, object storage for avatars, analytics pipeline.

---

## Local vs production

| | Local | Production (planned) |
| --- | --- | --- |
| Frontend | Vite `:5174` proxy `/api` | Vercel or Railway static |
| Backend | Uvicorn `:8002` | Railway Nixpacks |
| Database | Compose Postgres | Supabase or Railway Postgres |

Ports **5174 / 8002** avoid colliding with CalTrack (`5173` / `8001`).
