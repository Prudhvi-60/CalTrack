# CalTrack Architecture

CalTrack uses a three-tier design. The browser never opens PostgreSQL or Gemini; only FastAPI does.

```text
                    ┌───────────────────┐
                    │   CalTrack User   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌───────────────────┐
                    │ React + TypeScript│
                    │     Frontend      │
                    └─────────┬─────────┘
                              │ REST /api/v1
                              ▼
                    ┌───────────────────┐
                    │ FastAPI Backend   │
                    │      Python       │
                    └──────┬─────┬──────┘
                           │     │
                    ┌──────┘     └──────────┐
                    ▼                       ▼
             ┌─────────────┐         ┌─────────────┐
             │ PostgreSQL  │         │ Gemini AI   │
             │ + Alembic   │         │ (server)    │
             └─────────────┘         └─────────────┘
```

- Frontend: React + Vite + TypeScript. Axios to `/api/v1/*` only.
- Backend: FastAPI. JWT access tokens in memory on the client; refresh tokens are HttpOnly cookies. API keys stay in backend environment variables.
- Database: PostgreSQL via SQLAlchemy. Schema via Alembic. Production hosted Postgres is documented in [DEPLOYMENT.md](DEPLOYMENT.md). Authentication is FastAPI JWT, not a third-party auth product.
- Domain math (macros, remaining, trends, period goal targets) lives in `backend/app/utils/nutrition.py` and nutrition services.
- Vision, chat, and PDF parsing are backend services. Food-photo analysis uses a multimodal LLM for estimated nutrition JSON; labels extract printed values. Chat tools call existing meal/goal/nutrition services after Pydantic validation.

See [requirements-checklist.md](requirements-checklist.md) for the assignment review.
See the root [README.md](../README.md) for live URLs, demo, and local setup.
