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

**Live application:** [https://frontend-production-15c16.up.railway.app](https://frontend-production-15c16.up.railway.app)

**Sign in:** [https://frontend-production-15c16.up.railway.app/login](https://frontend-production-15c16.up.railway.app/login)

**API documentation:** [https://caltrack-production-c5cd.up.railway.app/docs](https://caltrack-production-c5cd.up.railway.app/docs)

**API health:** [https://caltrack-production-c5cd.up.railway.app/health](https://caltrack-production-c5cd.up.railway.app/health)

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

Local seed user (after `python -m scripts.seed` — **not** for the public Railway site): `demo@caltrack.app` / `DemoPass123!`

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

Placeholders and comments: [`.env.example`](.env.example), [`backend/.env.example`](backend/.env.example), [`frontend/.env.example`](frontend/.env.example). Deployment steps: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

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
| Live site will not sign in | Register a new account on the Railway website URL above |
| API docs open, website cannot load data | Website origin must be allowed in `FRONTEND_URL` / `CORS_ORIGINS` |
| Photo analysis fails | JPEG, PNG, or WebP, under 5 MB; Gemini must be set on the API |
| Local login works then drops | Keep `VITE_API_URL` empty so the Vite proxy is used |
