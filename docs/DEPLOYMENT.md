# Deployment

CalTrack production target:

- **Frontend:** Vercel (React + Vite)
- **Backend:** Railway (FastAPI / uvicorn)
- **Database:** Supabase PostgreSQL
- **AI:** Google Gemini (called only from Railway)

The browser talks only to FastAPI. FastAPI uses SQLAlchemy and Alembic against Supabase Postgres. Do **not** use the Supabase JavaScript client, `anon` key, or `service_role` key in the frontend.

```
React (Vercel)
    ↓ HTTPS
FastAPI (Railway)
    ↓ SQLAlchemy + Alembic
Supabase PostgreSQL
```

Authentication stays FastAPI JWT. Supabase is hosted Postgres only.

---

## 1. Create a Supabase project

1. Open [supabase.com](https://supabase.com) and create a project.
2. Wait until the database is ready.
3. You do **not** need Supabase Auth, Storage, or Row Level Security for CalTrack tables. The API enforces per-user access.

---

## 2. Get `DATABASE_URL`

1. Supabase dashboard → **Project Settings → Database**.
2. Open **Connect**.
3. Copy the **URI** connection string.
4. For Railway’s long-lived FastAPI process, choose **Session pooler (port 5432)**.
5. Transaction pooler (**port 6543**) works but is not preferred (PgBouncer transaction mode / NullPool).

Paste the URI into Railway as `DATABASE_URL`. You may also use `SUPABASE_DATABASE_URL`.

The backend rewrites `postgres://` to `postgresql+psycopg://` and adds `sslmode=require` for Supabase hosts.

Never commit this URI. Never put it in Vercel or `VITE_*`.

---

## 3. Railway environment variables

API service → **Variables**:

| Key | Value |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `INFO` |
| `DATABASE_URL` | Supabase Session pooler URI |
| `JWT_SECRET_KEY` | at least 32 random characters (not the development default) |
| `GEMINI_API_KEY` | Gemini key |
| `AI_PROVIDER` | `Gemini` |
| `AI_MODEL` | `gemini-3.1-flash-lite` (or the model your Google project can call) |
| `FRONTEND_URL` | Vercel origin, e.g. `https://caltrack.vercel.app` |
| `CORS_ORIGINS` | same as `FRONTEND_URL` |
| `COOKIE_SECURE` | `true` |
| `COOKIE_SAMESITE` | `none` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14` |

Railway injects `PORT`. Do not set `PORT` yourself.

---

## 4. Run Alembic migrations

Schema is created **only** with Alembic. Production startup does not drop or recreate tables.

Railway `backend/railway.toml` already runs:

```bash
alembic upgrade head
```

before each deploy.

Manual fallback in a Railway shell (from the `backend` directory):

```bash
alembic current
alembic heads
alembic upgrade head
```

Expected head: `0004_ai_feedback`.

Do not run `alembic downgrade` on production data. Do not use `Base.metadata.drop_all()`.

---

## 5. Seed data

Nutrition lookup foods live in `backend/app/data/nutrition_foods.json` (not Postgres). No extra seed is required for food matching.

Optional **demo user** (local or a throwaway Supabase project only):

```bash
cd backend
python -m scripts.seed
```

That creates `demo@caltrack.app`. Do not seed production with demo passwords.

---

## 6. Test database connectivity

After deploy:

- `GET https://<railway-host>/health` → process up (`{"status":"ok"}`)
- `GET https://<railway-host>/health/ready` → Postgres (`{"status":"ok","database":"connected"}`)
- Same paths under `/api/v1/...`

If the database is down, `/health/ready` returns a server error. It never returns the connection string.

Startup logs may include `Database URL: configured`. They never print the URI or password.

---

## 7. Deploy the backend

1. GitHub repo connected to Railway.
2. **Root Directory:** `backend`
3. Builder: Nixpacks (`backend/railway.toml`) or the existing `backend/Dockerfile`.
4. **Start command:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

5. Generate a public domain.
6. Confirm `/health` and `/docs`.

---

## 8. CORS

Set `FRONTEND_URL` (and `CORS_ORIGINS`) to the exact Vercel origin, no trailing slash.

Local development still allows `http://localhost:5173` via development defaults. Production ignores those localhost defaults.

---

## 9. Connect Vercel

1. Import the same GitHub repo.
2. **Root Directory:** `frontend`
3. Build: `npm run build`. Output: `dist`.
4. Set `VITE_API_URL` to the Railway origin with **no** trailing slash and **no** `/api/v1` suffix.
5. Redeploy after changing `VITE_API_URL` (it is baked in at build time).

Do not set `DATABASE_URL`, `JWT_SECRET_KEY`, or `GEMINI_API_KEY` on Vercel.

---

## 10. Security

- `.gitignore` already ignores `.env` / `.env.*` and keeps `*.env.example`.
- Frontend never receives database credentials.
- Keep using FastAPI JWT. Do not switch to Supabase Auth unless you explicitly choose to later.

More Railway/Vercel screenshots and checklists: [DEPLOYMENT_VERCEL_RAILWAY.md](DEPLOYMENT_VERCEL_RAILWAY.md).
