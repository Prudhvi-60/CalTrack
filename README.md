# CalTrack

Personal calorie tracker for daily nutrition, meals, goals, reports, and optional AI food scanning.

AI nutrition values are estimates. Users must review and confirm them before anything is saved.

## Architecture

```
React (Vite)  →  REST /api/v1  →  FastAPI  →  PostgreSQL
                                      ↓
                                 AI provider
```

The browser talks **only** to the FastAPI REST API. It never opens PostgreSQL or the AI provider. Access JWTs stay in memory; refresh tokens are HttpOnly cookies on the API origin.

**Local**

```
Vite :5173  --proxy /api-->  FastAPI :8001  →  PostgreSQL (local or Supabase)
```

**Production**

```
Internet → Vercel (React + Vite)
              HTTPS
         Railway (FastAPI)
              ├─ PostgreSQL (Supabase)
              └─ AI provider
```

## Local Development

Prerequisites: Python 3.12+, Node 20+, PostgreSQL 16 (or Docker), Git.

```bash
git clone <your-github-repo>
cd CalTrack
copy .env.example .env
copy frontend\.env.example frontend\.env
```

Leave `VITE_API_URL` empty locally so Vite proxies `/api` to the backend.

```bash
docker compose up postgres -d
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173  
API docs: http://127.0.0.1:8001/docs  
Health: http://127.0.0.1:8001/health

Optional full Docker stack: `docker compose up --build`.

## Production Architecture

| Piece | Host | Role |
| --- | --- | --- |
| Frontend | Vercel | React + Vite static `dist/` |
| Backend | Railway | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Database | Supabase PostgreSQL | `DATABASE_URL` / `SUPABASE_DATABASE_URL` |
| AI | Gemini | Called only from Railway |

Do not put `DATABASE_URL`, `JWT_SECRET_KEY`, or `GEMINI_API_KEY` in Vercel or in frontend source.

Step-by-step launch: [docs/DEPLOYMENT_VERCEL_RAILWAY.md](docs/DEPLOYMENT_VERCEL_RAILWAY.md).

## GitHub Setup

1. Create a private GitHub repository.
2. Confirm `.env` is gitignored.
3. Push the project. Do not commit secrets.
4. Connect that repo to Railway and Vercel.

## Railway Setup

1. New project → deploy from GitHub.
2. **Root Directory:** `backend`
3. Railway reads `backend/railway.toml`.
4. **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Set `DATABASE_URL` on the **API** service to the **Supabase Session pooler** URI (port 5432), or `SUPABASE_DATABASE_URL`. Do not use `${{Postgres.DATABASE_URL}}`.
6. Set the other variables below.
7. `preDeployCommand` runs `alembic upgrade head`.
8. Generate a public domain. Open `https://<service>.up.railway.app/health`.

## Vercel Setup

1. New Project → import the GitHub repo.
2. Framework: Vite. **Root Directory:** `frontend`
3. Build: `npm run build`. Output: `dist`. Install: `npm install`
4. `frontend/vercel.json` rewrites unknown paths to `index.html`.
5. Set `VITE_API_URL` to the Railway origin **without** a trailing slash.
6. Redeploy after changing `VITE_API_URL` (it is baked in at build time).

## Environment Variables

### Frontend (Vercel)

| Variable | Local | Production |
| --- | --- | --- |
| `VITE_API_URL` | empty (proxy) | `https://<railway-host>` |
| `VITE_API_TIMEOUT_MS` | `30000` | `30000` |

Legacy name `VITE_API_BASE_URL` is still read if `VITE_API_URL` is unset.

### Backend (Railway)

| Variable | Notes |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `INFO` |
| `DATABASE_URL` | Supabase Postgres URI (Session pooler `:5432`). Alias: `SUPABASE_DATABASE_URL` |
| `JWT_SECRET_KEY` | Long random secret (required; app refuses the default in production) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14` |
| `COOKIE_SECURE` | `true` |
| `COOKIE_SAMESITE` | `none` (cross-site Vercel ↔ Railway) |
| `FRONTEND_URL` | Vercel origin, e.g. `https://<project>.vercel.app` |
| `CORS_ORIGINS` | Same as `FRONTEND_URL` |
| `GEMINI_API_KEY` | Google Gemini secret (server only) |
| `AI_MODEL` | `gemini-2.5-flash-lite` |

Placeholders: `.env.example`, `backend/.env.example`, `frontend/.env.example`.

## Database Migration

Production schema is created **only** with Alembic. `Base.metadata.create_all()` is not used.

`backend/railway.toml` runs `alembic upgrade head` before each deploy. Manual fallback in Railway shell:

```bash
alembic upgrade head
```

Never run `alembic downgrade` on production data unless you intend to drop tables.

## CORS Configuration

FastAPI allows only origins in `CORS_ORIGINS` plus `FRONTEND_URL`. Credentials are enabled. Wildcards are ignored. Update both variables when you add a custom domain.

## AI Configuration

The scanner and chat call the provider from Railway. Missing keys return `AI_NOT_CONFIGURED` (503). Timeouts, rate limits, and invalid JSON become structured API errors without provider payloads.

## Health Checks

| URL | Auth | Meaning |
| --- | --- | --- |
| `GET /health` | no | `{"status":"ok"}` |
| `GET /health/ready` | no | process + PostgreSQL |
| `GET /health/db` | no | same as ready |

## Troubleshooting

- **Login works, then 401 after 15 minutes:** refresh cookie blocked as third-party. Confirm `COOKIE_SAMESITE=none`, `COOKIE_SECURE=true`, CORS credentials, and `withCredentials`. A custom domain for both apps is the durable fix.
- **CORS error:** Vercel origin missing from `FRONTEND_URL` / `CORS_ORIGINS` (no trailing slash).
- **Blank API calls on Vercel:** `VITE_API_URL` empty at build time; set it and redeploy.
- **Database SSL / driver errors:** Supabase URIs get `sslmode=require`. Use Session pooler `:5432` for FastAPI. Port `:6543` is transaction mode.
- **Migration failed:** Railway shell → `alembic current` then `alembic upgrade head`.

## Security Notes

- HttpOnly refresh cookie; access token in memory only.
- Production cookies are Secure + SameSite=None for split Vercel/Railway hosts.
- Users can only read their own meals, goals, nutrition, and AI feedback.
- Uploads are sniffed as JPEG/PNG/WEBP, size-capped, dimension-capped, and stored under generated names when opted in.
- Do not log passwords, JWTs, refresh tokens, or API keys.
- Rotate `JWT_SECRET_KEY` if it was ever committed or shared.

## Demo

After `python -m scripts.seed` locally:

- Email: `demo@caltrack.app`
- Password: `DemoPass123!`

Do not seed demo credentials into production unless you intend to.
