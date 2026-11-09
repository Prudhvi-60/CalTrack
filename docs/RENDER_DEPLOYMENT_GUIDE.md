# Render deployment guide

## Overview

This guide configures a Render Web Service for CalTrack while preserving the existing architecture:

- Frontend: Vercel
- Backend: Render Web Service
- Database: Neon PostgreSQL
- AI: Gemini-first, optional Hugging Face remains off by default

The repository includes `render.yaml` for the backend service. Applying the Blueprint configures Render; it does not change the Vercel frontend or database.

## 1. Repository and root directory

Use the GitHub repository as the source, then apply `render.yaml`. The Render web service root directory must be:

```text
backend
```

This is required because the actual FastAPI application entry point is in `backend/app/main.py`.

## 2. Build command

Use:

```bash
pip install -r requirements.txt
```

Run from the backend directory.

## 3. Start command

Use the service’s environment `PORT` variable and start the app with Uvicorn:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

This is the correct path when the app is built from the `backend` root directory.

## 4. Health check

Recommended health-check path:

```text
/health
```

This checks process health without requiring a live AI provider. Use `/health/ready` for deeper readiness validation after the app is already running.
The liveness response is `{"status":"healthy"}`.

If Render says `requirements.txt` cannot be found, check the deployed service's Root Directory. It must be `backend`, because the dependency file is `backend/requirements.txt`; do not create a duplicate in the repository root.

## 5. Environment variables

Set the following environment variables in the Render dashboard or use the references in `render.yaml`. Render generates `JWT_SECRET_KEY`; enter the database and Gemini secrets in the dashboard.

Required:

```text
ENVIRONMENT=production
DATABASE_URL=postgresql://... (Neon URL)
JWT_SECRET_KEY=replace-with-a-long-random-secret
GEMINI_API_KEY=your-gemini-key (required for AI features)
AI_PROVIDER=Gemini
AI_MODEL=gemini-3.1-flash-lite
FRONTEND_URL=https://your-vercel-app.vercel.app
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

Optional:

```text
LOG_LEVEL=INFO
HUGGINGFACE_API_KEY=
HUGGINGFACE_MODEL=google/gemma-2-2b-it
ENABLE_HUGGINGFACE=false
SMOLAGENTS_ENABLED=false
GRADIO_ENABLED=false
```

Important:

- Keep Gemini as the default provider.
- Leave optional AI integrations disabled unless explicitly enabled.
- Do not place secrets in the repository or in rendered docs.

## 6. Neon database configuration

Keep Neon as the database provider.

Recommended configuration:

- Use the existing Neon connection string as `DATABASE_URL`.
- Ensure the database URL is in a format accepted by SQLAlchemy + psycopg.
- Keep SSL enabled for the remote Neon endpoint.
- Do not change or recreate the database during migration preparation.
- Do not run Alembic migrations against production without explicit approval.

## 7. CORS and frontend alignment

The frontend uses the `VITE_API_URL` variable. Set it in Vercel Project Settings → Environment Variables to the Render public API origin (no trailing slash and no `/api/v1` suffix), then redeploy.

The frontend application reads:

```ts
VITE_API_URL
```

The backend accepts the origin in:

```text
FRONTEND_URL
CORS_ORIGINS
```

Set both `FRONTEND_URL` and `CORS_ORIGINS` to the exact production Vercel origin. The production CORS list may also include:

- the Vercel app origin
- any approved preview origin
- no unrestricted wildcard in authenticated production flows

The backend already defines `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, and `POST /api/v1/auth/refresh`. The frontend uses POST for those operations. A 405 from Vercel occurs when the frontend is built without `VITE_API_URL` and posts to the frontend host rather than the FastAPI API.

## 8. Gradio handling

Gradio remains a separate concern and should not be required for the FastAPI backend startup.

Recommended treatment:

- keep `GRADIO_ENABLED=false` by default
- launch Gradio only as a dedicated service when explicitly needed
- restrict access and avoid exposing secrets
- do not depend on Gradio for the main API logic

## 9. Service lifecycle

Render handles the HTTP web service lifecycle. The app should:

- bind to `0.0.0.0`
- use the Render-assigned `PORT`
- initialize configuration on startup
- fail gracefully when a non-critical optional AI provider is unavailable
- avoid logging secrets

## 10. Rollback plan

Keep the Railway service active during the migration window.

Rollback steps:

1. Leave the current Railway backend running.
2. Keep the existing Vercel frontend configuration in place until staging validation is approved.
3. Do not delete the Railway app or config until the Render staging validation is approved.
4. If the Render service fails, restore the previous Railway backend URL in the frontend and redeploy Vercel.

## 11. Validation checklist before a staging deployment

Before any staging deployment to Render, confirm:

- the repo root is correct
- backend root directory is correct
- build command is valid
- start command is valid
- environment variables are defined
- `DATABASE_URL` points to Neon
- `JWT_SECRET_KEY` is set
- Gemini remains enabled and default
- optional AI integrations remain off by default
- health endpoint responds
- readiness endpoint responds when PostgreSQL is available
- frontend API URL is updated only after approval

## 12. Final validation

- Confirm the Render Root Directory is `backend`.
- Confirm the Render health check returns `{"status":"healthy"}` at `/health`.
- Set Vercel `VITE_API_URL` to the Render public API origin and redeploy.
- Confirm `FRONTEND_URL` and `CORS_ORIGINS` exactly match the Vercel site origin.
- Verify registration, login, and refresh against `/api/v1/auth/*`.
