# Railway to Render migration audit

## Scope

This document audits the current CalTrack deployment assumptions and prepares the application for a Render Web Service deployment while keeping the existing Neon PostgreSQL, Vercel frontend, and Gemini-first architecture in place.

This is a migration-preparation document only. No production deployment or infrastructure changes were made.

## Existing Railway configuration

Current repository evidence:

- `backend/railway.toml` exists and defines the Railway deployment contract.
- Railway build is Nixpacks-based.
- Railway deploy command is:
  `sh -c 'uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}'`
- Railway pre-deploy step runs:
  `alembic upgrade head`
- Railway health check path is `/health`.
- Root directory for the backend is `backend/`.

## Backend working directory and start command

The app is a FastAPI project rooted in `backend/`.

Verified application entry point:

- `backend/app/main.py`
- FastAPI object is created in `app.main:app`
- The module path is valid when the working directory is `backend/`

The current working-directory-sensitive production command is therefore:

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

This is the correct pattern for Render, provided Render sets the `PORT` environment variable.

## Build command

The current backend dependency installation path is:

```bash
cd backend
pip install -r requirements.txt
```

No Docker build is required unless the deployment target explicitly chooses to package the app via container files. The repo does not rely on a Docker-only deployment model for the web service.

## Health-check endpoints

Health endpoints exist in `backend/app/api/routes/health.py`:

- `/health` — process liveness
- `/health/ready` — verifies the API can reach PostgreSQL
- `/health/db` — runs `SELECT 1` against the database

These are the correct Render-compatible health probes for an application that depends on PostgreSQL.

## Required environment variables

The application reads these settings from environment variables via `backend/app/core/config.py` and the `.env.example` files.

Required for the web service:

- `DATABASE_URL`
- `ENVIRONMENT`
- `JWT_SECRET_KEY`
- `GEMINI_API_KEY`
- `AI_PROVIDER`
- `AI_MODEL`
- `FRONTEND_URL`
- `CORS_ORIGINS`

Optional but supported:

- `HUGGINGFACE_API_KEY`
- `HUGGINGFACE_MODEL`
- `ENABLE_HUGGINGFACE` (default: false)
- `SMOLAGENTS_ENABLED` (default: false)
- `GRADIO_ENABLED` (default: false)
- `LOG_LEVEL`
- `DB_POOL_SIZE`
- `DB_MAX_OVERFLOW`
- `DB_POOL_TIMEOUT`
- `DB_POOL_RECYCLE`

Important: the application keeps Gemini as the default AI provider and leaves optional Hugging Face/SmolAgents/Gradio disabled unless explicitly configured.

## Database connectivity requirements

The backend expects PostgreSQL and uses SQLAlchemy + Alembic.

Current constraints from existing project configuration:

- `DATABASE_URL` is required in non-local production.
- Supabase/Neon is the existing database provider.
- `sslmode=require` is added for remote PostgreSQL hosts unless the hostname is local or Railway-private.
- The app accepts Neon/Supabase-style connection strings without exposing passwords in logs.
- Render must provide the database URL to the web service without changing the database provider.

## Background job requirements

The current application does not require a background worker for the primary API workflow.

The app performs:

- image analysis
- PDF parsing
- chat and nutrition logic
- database reads/writes
- optional AI provider dispatch

These operations are handled in the web process and are not obviously queued jobs requiring Celery or Redis. No background worker should be introduced solely for the migration unless the application later adds a clear asynchronous workload.

## Render migration risks

Primary risks to manage:

1. Render service must run in the backend root directory (`backend/`), not the repo root.
2. The app expects `PORT` from the hosting platform; Render supplies this automatically.
3. CORS must permit the Vercel frontend and any approved preview domains.
4. The backend must not rely on local Windows-only paths or local `.env` files in production.
5. Optional AI providers must remain off unless explicitly configured.
6. Render health checks should not rely on AI availability; they should only check process and database readiness.
7. The web service must not attempt to manage the database itself beyond normal initialization and runtime reads. Neon remains the source of truth.

## Verdict

Status: RENDER CONFIGURATION PREPARATION READY FOR STAGING REVIEW

The project is structurally prepared for a Render web service migration, but actual deployment still requires explicit user approval and a staging environment configuration step. No production resources were touched.
