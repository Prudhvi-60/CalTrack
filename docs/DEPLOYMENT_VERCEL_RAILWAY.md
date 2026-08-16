# CalTrack — Vercel frontend + Railway backend

This repository is **deployment-ready**. It is **not** deployed until you complete these steps. Do not put secrets in git.

```
Internet → Vercel (React + Vite)
              HTTPS
         Railway FastAPI
              ├─ Railway PostgreSQL
              └─ AI provider
```

Local development is unchanged: Vite `:5173` proxies `/api` to FastAPI `:8000` and local PostgreSQL.

## Production test checklist

- [ ] GitHub repository pushed
- [ ] No secrets committed (`git ls-files .env` is empty)
- [ ] Railway backend created
- [ ] Railway environment variables configured
- [ ] PostgreSQL configured (Railway plugin)
- [ ] Alembic migrations executed
- [ ] Railway backend deployed
- [ ] `/health` works
- [ ] `/docs` works
- [ ] Railway public domain generated
- [ ] Vercel project created
- [ ] Vercel root directory = `frontend`
- [ ] Vercel build succeeds
- [ ] `VITE_API_URL` configured
- [ ] Vercel deployment succeeds
- [ ] CORS configured
- [ ] Registration works
- [ ] Login works
- [ ] Logout works
- [ ] Protected routes work
- [ ] Meal creation works
- [ ] Meal retrieval works
- [ ] Goals work
- [ ] Reports work
- [ ] AI scanner works
- [ ] Image upload works
- [ ] Data persists
- [ ] Application works on mobile

---

## 1. GitHub repository

1. github.com → **New repository** (private recommended).
2. Locally:

   ```bash
   git remote add origin https://github.com/<you>/<repo>.git
   git push -u origin main
   ```

3. Confirm secrets are not tracked:

   ```bash
   git ls-files .env frontend/.env backend/.env
   ```

   That command must print nothing.

---

## 2. Railway project creation

1. [railway.app](https://railway.app) → **Login** → **New Project**.
2. **Deploy from GitHub repo** → select CalTrack.
3. If Railway creates a service from the repo root, open the service → **Settings → Root Directory** → `backend`.
4. Nixpacks should detect Python from `backend/requirements.txt`. Python 3.12 is set in `backend/.python-version`.

---

## 3. Railway backend configuration

| Setting | Value |
| --- | --- |
| Root directory | `backend` |
| Builder | Nixpacks (`backend/railway.toml`) |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Pre-deploy | `alembic upgrade head` |
| Health check | `/health` |

Do not hard-code port 8000. Railway injects `PORT`.

Existing `backend/Dockerfile` is optional. Prefer Nixpacks unless you explicitly choose Docker in the service settings.

---

## 4. Railway environment variables

Service → **Variables**. Set:

| Key | Value |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `INFO` |
| `DATABASE_URL` | usually **shared** from the Postgres plugin |
| `JWT_SECRET_KEY` | long random string (not the example default) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `14` |
| `COOKIE_SECURE` | `true` |
| `COOKIE_SAMESITE` | `none` |
| `FRONTEND_URL` | set after Vercel exists |
| `CORS_ORIGINS` | same as `FRONTEND_URL` |
| `GEMINI_API_KEY` | your Gemini API key |
| `AI_MODEL` | `gemini-2.5-flash-lite` |

Optional pool settings if you need to override defaults: `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=10`.

---

## 5. PostgreSQL setup

1. In the same Railway project: **New** → **Database** → **PostgreSQL**.
2. Open the Postgres service → **Variables**. Copy `DATABASE_URL`, or **Variable reference** it into the API service as `DATABASE_URL`.
3. The API rewrites `postgres://` to `postgresql+psycopg://`. Public proxy hosts get `sslmode=require`. Private `*.railway.internal` hosts do not.

Do not enable a browser/Supabase client. SQLAlchemy on Railway is the only database access path.

---

## 6. Alembic migrations

`backend/railway.toml` sets `preDeployCommand = "alembic upgrade head"`.

If a deploy fails on migrate, open the API service **Settings → One-off command** or shell:

```bash
alembic upgrade head
alembic current
```

Expected current revision: `0004_ai_feedback`.

Do not use `Base.metadata.create_all()` and do not `alembic downgrade` on production data.

---

## 7. Railway domain generation

1. API service → **Settings → Networking → Generate Domain**.
2. Copy the public origin, for example `https://<name>.up.railway.app` (no trailing slash).
3. Test:

   - `https://<railway-domain>/health` → `{"status":"ok"}`
   - `https://<railway-domain>/health/ready`
   - `https://<railway-domain>/docs`

---

## 8. Vercel project creation

1. [vercel.com](https://vercel.com) → **Add New → Project**.
2. Import the same GitHub repository.

---

## 9. Vercel root directory

**Root Directory:** `frontend`

---

## 10. Vercel build settings

| Setting | Value |
| --- | --- |
| Framework | Vite |
| Install | `npm install` |
| Build | `npm run build` |
| Output | `dist` |

`frontend/vercel.json` already rewrites `/login`, `/dashboard`, `/meals`, `/ai-scan`, and other client routes to `index.html`.

---

## 11. Vercel environment variable

Project → **Settings → Environment Variables** → Production:

| Key | Value |
| --- | --- |
| `VITE_API_URL` | `https://<railway-domain>` |

No `/api/v1` suffix. No trailing slash. Do not add `GEMINI_API_KEY` here.

Redeploy after saving (Vite inlines `VITE_*` at build time).

---

## 12. CORS configuration

After the Vercel URL exists (`https://<project>.vercel.app`):

1. Railway API variables:
   - `FRONTEND_URL=https://<project>.vercel.app`
   - `CORS_ORIGINS=https://<project>.vercel.app`
2. Redeploy the Railway service if variables do not hot-reload.
3. Custom domain later: change these three values (`FRONTEND_URL`, `CORS_ORIGINS`, `VITE_API_URL`). No source change.

Wildcards are not allowed with credentialed cookies.

---

## 13. Authentication testing

1. Open the Vercel URL → **Register** → **Login**.
2. Confirm `/dashboard` loads (protected).
3. **Logout** → login again.
4. Wait past 15 minutes or clear the access token in memory by refresh: session should restore via the HttpOnly cookie if the browser allows cross-site cookies (`SameSite=None; Secure`).

If refresh fails in Chrome, the access token still works until expiry. A custom domain for both apps is the durable cookie fix.

---

## 14. AI testing

1. Railway has `GEMINI_API_KEY` set.
2. Vercel **does not**.
3. On `/ai-scan`, upload a JPEG/PNG/WEBP under 5 MB.
4. Review the result, then save a meal.
5. In browser DevTools, API calls go to the Railway host only — never to Google AI.

---

## 15. Production troubleshooting

| Symptom | Check |
| --- | --- |
| CORS error | Exact Vercel origin in `FRONTEND_URL` / `CORS_ORIGINS`, no trailing slash |
| Network error on Vercel | `VITE_API_URL` set, then **Redeploy** |
| 503 `AI_NOT_CONFIGURED` | `GEMINI_API_KEY` on Railway |
| `/health/ready` fails | Postgres plugin linked; `DATABASE_URL` present |
| 401 after a few minutes | `COOKIE_SAMESITE=none`, `COOKIE_SECURE=true` |
| Migration error | Railway shell `alembic upgrade head` |
| App 404 on `/login` | Confirm `frontend/vercel.json` is in the Vercel root |

---

## Exact dashboard values

### Railway

```
Root directory:     backend
Build:              Nixpacks (pip install from requirements.txt)
Start command:      uvicorn app.main:app --host 0.0.0.0 --port $PORT
Pre-deploy:         alembic upgrade head
Healthcheck:        /health

DATABASE_URL=            (from Postgres plugin)
JWT_SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=14
COOKIE_SECURE=true
COOKIE_SAMESITE=none
ENVIRONMENT=production
LOG_LEVEL=INFO
FRONTEND_URL=https://<vercel-domain>
CORS_ORIGINS=https://<vercel-domain>
GEMINI_API_KEY=
AI_MODEL=gemini-2.5-flash-lite
```

### Vercel

```
Root directory:     frontend
Install command:    npm install
Build command:      npm run build
Output directory:   dist

VITE_API_URL=https://<railway-domain>
```
