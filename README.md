# CalTrack

CalTrack is an AI-powered calorie and nutrition tracking application. Users register an account, log meals (by hand, photo, or PDF), set daily goals, and review calories, macros, micronutrients, and history on a dashboard and reports. The website talks only to a FastAPI REST API; the API stores data in PostgreSQL and calls Google Gemini when a photo, chat, or PDF needs analysis.

**AI nutrition values are estimates.** Review them before you save. Nothing from a photo or PDF is stored until you confirm.

[![GitHub](https://img.shields.io/badge/GitHub-Prudhvi--60%2FCalTrack-181717?logo=github)](https://github.com/Prudhvi-60/CalTrack)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-TypeScript-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)

---

## Demo

[![CalTrack Demo](https://img.youtube.com/vi/mG2mS4CW_TU/maxresdefault.jpg)](https://youtu.be/mG2mS4CW_TU)

**Watch the full CalTrack demo on YouTube:** [https://youtu.be/mG2mS4CW_TU](https://youtu.be/mG2mS4CW_TU)

A copy of the walkthrough is also in the repository: [docs/demo/Demo_Video.mp4](docs/demo/Demo_Video.mp4)

**Deployment:** The backend targets Render and the frontend targets Vercel. Public URLs are set in those dashboards and are not embedded in the repository.

**Source:** [https://github.com/Prudhvi-60/CalTrack](https://github.com/Prudhvi-60/CalTrack)

On the live site, **create an account** (Register), then sign in. Meals and goals belong only to that account.

---

## Features

- **User authentication** — register, sign in, sign out, update name/password; JWT access tokens in memory and HttpOnly refresh cookies
- **Private per-user data** — meals, goals, and nutrition are scoped to the signed-in user
- **Meal logging** — breakfast, lunch, dinner, snacks with food name, quantity, calories, macros, and micronutrients
- **Meal history** — filter by date, date range, meal type, and search; paginated lists
- **Daily goals** — calorie, protein, carb, and fat targets, optional weight goal, remaining vs actual
- **Nutrition dashboard** — today’s intake, remaining macros, weekly calorie trend, meal list
- **Reports and charts** — calorie trends, macro breakdown, micronutrient summary, goal vs actual (7 / 30 / 90 days)
- **AI food scan** — upload a plate photo or nutrition label; review estimates, then save
- **Nutrition assistant (chat)** — text questions and actions (log meals, remaining calories, summaries); photos go to AI Scan
- **PDF import** — upload a food diary or meal plan, review extracted meals, then save
- **REST API** — FastAPI `/api/v1/*` with interactive OpenAPI docs
- **PostgreSQL persistence** — SQLAlchemy + Alembic (no schema created from the frontend)
- **Health checks** — `/health` and readiness endpoints
- **Responsive frontend** — React + TypeScript, usable on desktop and mobile

---

## How it works

1. The user registers or logs in on the website.
2. They set goals and add meals by form, **AI Scan**, **Import**, or (for some actions) **Chat**.
3. The frontend sends HTTPS requests to the FastAPI REST API (`/api/v1`). It never opens the database or Gemini.
4. The API authenticates the user, validates input, and applies per-user access rules.
5. When a photo, chat, or PDF needs AI, the backend calls Gemini and returns structured results.
6. Calories and macros are stored on confirm (or after chat tools pass server validation). Photo/PDF drafts are not saved until confirm.
7. Dashboard and Reports read stored meals and goals and show progress, trends, and history.

---

## Architecture

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
                              │ REST API
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
             │ (Alembic)   │         │ (server)    │
             └─────────────┘         └─────────────┘
```

| Layer | Technology | Role |
| --- | --- | --- |
| Frontend | React, Vite, TypeScript | UI only; Axios to `/api/v1` |
| Backend | FastAPI (Python 3.12) | Auth, meals, goals, nutrition, AI, import |
| Database | PostgreSQL | Users, meals, foods, goals, tokens |
| Migrations | Alembic | Schema changes (not `create_all` in production) |
| AI | Google Gemini | Called **only** from the API (scan, chat, PDF) |
| Auth | FastAPI JWT | Not a third-party login product |

Live deployment used in this README: frontend and API on Railway; production database is PostgreSQL (see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for hosted Postgres setup). More detail: [docs/architecture.md](docs/architecture.md).

### Repository layout

```text
CalTrack/
  frontend/     React + Vite website
  backend/      FastAPI application, Alembic, tests
  docs/         Architecture, deployment, requirements
  docs/demo/    Demo walkthrough video
```

---

## Getting started (local)

You need **Git**, **Python 3.12+**, **Node 20+**, and **PostgreSQL** (or Docker).

```bash
git clone https://github.com/Prudhvi-60/CalTrack.git
cd CalTrack
```

**Windows**

```bash
copy .env.example .env
copy frontend\.env.example frontend\.env
```

**macOS / Linux**

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Leave `VITE_API_URL` empty locally so the website uses the Vite `/api` proxy (same-site cookies work). Do not put database or Gemini secrets in `VITE_*` variables.

**Database + API**

```bash
docker compose up postgres -d
cd backend
python -m venv .venv
```

Windows: `.venv\Scripts\activate`  
macOS / Linux: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

**Website** (another terminal)

```bash
cd frontend
npm install
npm run dev
```

| Local | URL |
| --- | --- |
| Website | [http://localhost:5173](http://localhost:5173) |
| API docs | [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) |
| Health | [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health) |

Local seed user (after `python -m scripts.seed`): `demo@caltrack.app`. Set a unique `CALTRACK_DEMO_PASSWORD` of at least 12 characters before running the seed command; no default password is provided.

Optional: `docker compose up --build` runs the full stack.

### Tests

```bash
cd backend
pytest
cd ../frontend
npm test
npm run build
```

---

## Environment variables

Copy `.env.example` and `frontend/.env.example`. **Never commit real `.env` files.**

| Name | Where | Purpose |
| --- | --- | --- |
| `VITE_API_URL` | Frontend | Empty locally (proxy). Production: API origin, no trailing slash |
| `DATABASE_URL` | Backend | PostgreSQL URI (SQLAlchemy/Alembic only) |
| `JWT_SECRET_KEY` | Backend | Signing secret (required in production) |
| `FRONTEND_URL` / `CORS_ORIGINS` | Backend | Browser origin of the website |
| `GEMINI_API_KEY` | Backend | Gemini for scan, chat, and import |
| `AI_MODEL` | Backend | Model name used by the API |

Placeholders and comments: [`.env.example`](.env.example), [`backend/.env.example`](backend/.env.example), [`frontend/.env.example`](frontend/.env.example). Render deployment steps: [docs/RENDER_DEPLOYMENT_GUIDE.md](docs/RENDER_DEPLOYMENT_GUIDE.md).

---

## Assumptions

- Photo and chat nutrition is **estimated**, not lab-accurate. Scanner and PDF import require confirm before save; chat write tools save after server validation.
- Report days use **UTC** calendar dates, not the device timezone.
- Micronutrients are values you or AI enter; they are not a complete lab panel.
- PDF import works best with a readable diary or meal plan; messy scans may need edits on the review screen.
- Chat is **text only**. Food photos belong on AI Scan.
- If Gemini is not configured, scan/chat/import return a clear error instead of crashing.
- Assignment mapping and test evidence: [docs/requirements-checklist.md](docs/requirements-checklist.md).

---

## Troubleshooting

| Problem | What to try |
| --- | --- |
| Frontend cannot sign in | Check Vercel's `VITE_API_URL` and the backend's `FRONTEND_URL` / `CORS_ORIGINS` settings |
| API docs open, website cannot load data | Website origin must be allowed in `FRONTEND_URL` / `CORS_ORIGINS` |
| Photo analysis fails | JPEG, PNG, or WebP, under 5 MB; Gemini must be set on the API |
| Local login works then drops | Keep `VITE_API_URL` empty so the Vite proxy is used |

---

## Render deployment

### Backend layout and local setup

The existing FastAPI application is in `backend/app/main.py` and is served as `app.main:app` from the `backend` working directory. Routes live in `backend/app/api/routes/`; authentication is implemented in `auth.py`, SQLAlchemy models and schemas are in `backend/app/models/` and `backend/app/schemas/`, database access is in `backend/app/db/`, and Alembic migrations are in `backend/alembic/`. There is one backend application; do not create a second `main.py` at the repository root.

Use Python **3.12.8**, pinned by `backend/.python-version` (also recorded in `backend/runtime.txt`):

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Deploy the backend to Render

Create or update the Render service from the repository's `render.yaml` Blueprint. It sets the service root directory to `backend`, where `requirements.txt` actually lives. The build command is `pip install -r requirements.txt`; the start command is `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`. If the deploy log still runs `gunicorn your_application.wsgi`, the service has a stale Dashboard Start Command override: in Render, open **Settings → Build & Deploy → Start Command**, replace it with the command above, and save. If Render reports that it cannot find `requirements.txt`, its Root Directory is not `backend`; do not add a duplicate requirements file to the repository root.

Set these values in the Render dashboard:

| Variable | Value |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | Existing Neon PostgreSQL connection string |
| `JWT_SECRET_KEY` | Unique secret generated by Render (at least 32 characters) |
| `FRONTEND_URL` | Exact production Vercel origin, e.g. `https://your-app.vercel.app` |
| `CORS_ORIGINS` | Same exact Vercel origin; comma-separate any approved additional origins |
| `GEMINI_API_KEY` | Google Gemini key, required for AI features |
| `AI_PROVIDER` | `Gemini` |
| `AI_MODEL` | `gemini-3.1-flash-lite` or another available Gemini model |

Render provides `PORT`; do not define it yourself. Keep database and provider credentials only in Render's environment settings, never in the frontend or committed `.env` files.

### Connect the Vercel frontend

In Vercel Project Settings → Environment Variables, set `VITE_API_URL` to the Render API's public origin (for example `https://your-service.onrender.com`) with no trailing slash and no `/api/v1` suffix. Redeploy Vercel after setting it. Without this build-time variable, the frontend now refuses production API requests rather than sending `/api/v1/...` to the Vercel site and receiving static-site 405 responses. Keep `DATABASE_URL`, `JWT_SECRET_KEY`, and `GEMINI_API_KEY` off Vercel.

FastAPI's `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, and `POST /api/v1/auth/refresh` routes already match the frontend's POST requests. `/health` is the Render liveness check and returns `{"status":"healthy"}`; `/health/ready` additionally checks PostgreSQL. CORS allows credentialed requests only from the configured frontend origins, with the required HTTP methods and headers.

### Further Render references

The following guide and checklist document the deployment and cutover details:

- [docs/RAILWAY_TO_RENDER_MIGRATION_AUDIT.md](docs/RAILWAY_TO_RENDER_MIGRATION_AUDIT.md)
- [docs/RENDER_DEPLOYMENT_GUIDE.md](docs/RENDER_DEPLOYMENT_GUIDE.md)
- [docs/RENDER_ENVIRONMENT_VARIABLES.md](docs/RENDER_ENVIRONMENT_VARIABLES.md)
- [docs/RAILWAY_TO_RENDER_CUTOVER_CHECKLIST.md](docs/RAILWAY_TO_RENDER_CUTOVER_CHECKLIST.md)
- [render.yaml](render.yaml)
