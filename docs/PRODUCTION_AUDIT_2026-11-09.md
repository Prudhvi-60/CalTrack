# CalTrack production audit — 2026-11-09

## Overall status

**BLOCKED for production release.** Local code, database schema metadata, and frontend checks pass after the changes in this audit. A Render deployment and live workflow verification could not be completed because no Render service URL or connected Render control is available. The two production URLs still published in `README.md` return HTTP 404.

## Architecture inspected

- **Frontend:** React 19, TypeScript, Vite; entry point `frontend/src/main.tsx`, route tree `frontend/src/App.tsx`; Vercel SPA rewrite in `frontend/vercel.json`.
- **Backend:** FastAPI; application `backend/app/main.py` (`app.main:app`); route modules under `backend/app/api/routes/`.
- **Database:** PostgreSQL, SQLAlchemy 2, psycopg 3, Alembic revisions `0001_initial` through `0004_ai_feedback`.
- **Authentication:** bcrypt password hashes, bearer access tokens, refresh-token cookies, user-scoped routes; covered by backend auth tests.
- **External services:** Google Gemini from the backend. Hugging Face, SmolAgents, and Gradio are optional and disabled by default.
- **Uploads:** Multipart endpoints for food-image and PDF processing; size/type validation is applied in API/service code. Files are processed by the backend; no persistent object-storage service is configured.
- **Jobs:** No production scheduler or background worker is configured. Training scripts are command-driven.
- **Deployment:** Render Blueprint for the FastAPI service, Vercel config for the frontend, and Docker Compose for local PostgreSQL/development.

## Findings and changes

- Route pages were eagerly bundled. They now load on demand with a visible Suspense status; the largest generated chunk fell from about 963 KB to 424 KB.
- SQLAlchemy metadata did not describe the existing migration schema consistently: named uniqueness constraints and a composite refresh-token index were missing from metadata, and a feedback index name differed. Model metadata now matches the local migrated schema. No database objects were dropped or changed.
- Frontend dependency audit found vulnerable Axios, `follow-redirects`, Zod, Vitest, and `minimatch` versions. Axios and transitive dependencies were updated; Zod and Vitest were upgraded to patched major versions; a scoped `minimatch` override selects the patched release. Zod coercion options were updated for v4.
- Backend dependency audit found vulnerable JWT, multipart, Starlette, PDF, image, and other pinned versions. The backend now uses PyJWT with an explicit algorithm allow-list and updated FastAPI, Starlette, multipart, PDF, Pillow, dotenv, pytest, and related dependencies. SmolAgents was moved to an opt-in requirements file because Render disables it. Gradio was removed from Render's production requirements; its current release requires Pillow below the patched Pillow 13 used by production image handling, so the standalone demo remains outside the production environment.
- The development seed no longer contains a default password and refuses non-local databases before touching the session. The README no longer publishes the 404 Railway URLs or the old seeded password.
- Removed unused Python imports surfaced by Ruff.
- The root `.env` file is ignored by Git and is not tracked. Its contents were not included in this report. Deployment secrets remain environment-only.

## Verification

| Area | Status | Evidence |
| --- | --- | --- |
| Backend tests | PASS | `pytest -q`: 164 passed against the explicit local PostgreSQL URL after the dependency and SQLAlchemy metadata updates. The suite's DB fixture wraps test operations in rollback transactions. One Starlette deprecation warning recommends `httpx2` for `TestClient`; it did not affect the tests. |
| Backend startup/API smoke | PASS | FastAPI TestClient: `/health` 200, `/docs` 200, unauthenticated `/api/v1/meals` 401. No real Gemini request was made. |
| Python compile | PASS | `python -m compileall -q app`. |
| Python lint | PASS | `ruff check app --select E4,E7,E9,F --ignore F821`; `F821` is excluded because SQLAlchemy forward-reference annotations are string literals. |
| Local migration state | PASS | Local database is at `0004_ai_feedback`; `alembic check` reports no new upgrade operations. This does not establish the production database's revision. |
| Frontend tests | PASS | Vitest: 14 tests across 11 files. |
| Frontend lint | PASS | `npm run lint`. |
| Frontend production build | PASS | `npm run build`; route splitting removed the oversized-chunk warning. Rollup emits two harmless annotation-position notices from Zod 4. |
| Frontend dependency audit | PASS | `npm audit`: 0 vulnerabilities after the updates. |
| Python dependency audit | PASS | `pip-audit -r requirements.txt`: no known vulnerabilities in the Render production requirements. `requirements-experimental.txt` (SmolAgents) also audits clean. Gradio is excluded from production because its current Pillow constraint conflicts with patched production Pillow. |
| Production health/docs/auth | BLOCKED | No Render URL is configured in the repository or available through a connected Render account. README's legacy Railway backend and frontend URLs both return 404. |
| Production database/migrations | BLOCKED | No authorized production database verification or migration was run. |
| Live frontend/API/CORS/auth flows | BLOCKED | No current production frontend/backend URLs or Render/Vercel settings are available. |

An initial backend test command was stopped after confirming the default root `.env` resolves to a remote database. That run was not counted. The passing run explicitly used `localhost:5432`; no production migration, reset, or schema change was run. The seed guard was separately exercised against the configured remote target and rejected the operation before opening a database session.

## Render deployment configuration

`render.yaml` points to the right service: Python web service, root directory `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, and liveness path `/health`. Python is pinned to 3.12.8 by `backend/.python-version`. Render supplies `PORT`.

The Blueprint sets `autoDeploy: false`, so pushing code alone will not deploy. No Render public URL is recorded. It also does not run Alembic automatically. The production database revision must be checked in Render before deciding whether to run `alembic upgrade head`; the local database check is not a substitute.

## Manual production steps

1. In Render, select the CalTrack repository and deployment branch, confirm the service root is `backend`, and use the Blueprint start/build/health settings above.
2. Set `DATABASE_URL` to the existing PostgreSQL/Neon database, `FRONTEND_URL` and `CORS_ORIGINS` to the exact production Vercel origin, and `GEMINI_API_KEY` if AI features are required. Keep the Blueprint-generated `JWT_SECRET_KEY`; do not copy backend secrets to Vercel. `ENVIRONMENT`, `AI_PROVIDER`, and `AI_MODEL` are specified in `render.yaml`. Do not manually set Render's `PORT`.
3. Before applying a migration, inspect the Render database's Alembic revision and schema. Back up the database, then run `alembic upgrade head` only if the remote revision requires it. The repository migration path is forward-only; do not run downgrades or resets.
4. Deploy manually from Render because `autoDeploy` is disabled. Record the generated Render service URL.
5. In Vercel, set `VITE_API_URL` to that Render origin (no trailing slash and no `/api/v1`), then redeploy. Record the exact Vercel origin in Render's `FRONTEND_URL` and `CORS_ORIGINS`.
6. Verify Render reports the service live; check `/health`, `/health/ready`, `/docs`, browser CORS, registration/login, protected endpoints, and a dedicated test account before treating production as complete.

Production URLs, credentials, migration revision, deployment status, and live workflow results remain **BLOCKED / NOT VERIFIED** until those dashboard settings and URLs are available.
