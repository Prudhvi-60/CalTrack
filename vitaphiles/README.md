# Vitaphiles

**Stories worth remembering.**

Track the books you read, the films you watch, and the stories that stay with you.

Vitaphiles is a book + movie discovery platform (editorial, not a dashboard). It lives in `vitaphiles/` inside this GitHub repo so **CalTrack is unchanged**.

## Features (product)

See [docs/PRODUCT_REQUIREMENTS.md](docs/PRODUCT_REQUIREMENTS.md). Phase 1 is foundation only: app shell, database schema, health API.

## Architecture

React SPA → FastAPI `/api/v1` → PostgreSQL + (later) Google Books + TMDB. Details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Stack

React 19, TypeScript, Vite, Tailwind, TanStack Query, Axios, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL.

## Local setup

Vitaphiles uses **ports 5174 / 8002 / 5433** so it can run beside CalTrack (5173 / 8001 / 5432).

```bash
cd vitaphiles
cp .env.example .env
docker compose up postgres -d   # Postgres 16 on localhost:5433

cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8002
```

Without Docker, point `DATABASE_URL` at any PostgreSQL 16 database, then run the same Alembic and uvicorn commands.

```bash
cd vitaphiles/frontend
cp .env.example .env
# leave VITE_API_URL empty to use the Vite proxy to :8002
npm install
npm run dev
```

| | URL |
| --- | --- |
| Website | http://localhost:5174 |
| API docs | http://127.0.0.1:8002/docs |
| Health | http://127.0.0.1:8002/health |

## Environment

See `.env.example`. Never commit `.env`. Never put `TMDB_API_KEY` or `DATABASE_URL` in `VITE_*`.

## Migrations

```bash
cd vitaphiles/backend
alembic upgrade head
alembic revision -m "message"
```

## Deployment

Planned: frontend Vercel/Railway, API Railway, Postgres Supabase or Railway. [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Screenshots

_Placeholder — add product screenshots here._

## Demo video

_Placeholder — add a walkthrough URL here._
