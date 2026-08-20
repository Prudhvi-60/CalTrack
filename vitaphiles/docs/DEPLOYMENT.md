# Deployment (Vitaphiles)

Not deployed in Phase 1.

**Plan:**

| Piece | Target |
| --- | --- |
| Frontend | Vercel or Railway, `VITE_API_URL` = API origin (no `/api/v1` suffix) |
| Backend | Railway, `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Database | Supabase session pooler or Railway Postgres |
| Pre-deploy | `alembic upgrade head` |

CORS: exact frontend origin in `FRONTEND_URL` / `CORS_ORIGINS`. Cookie `SameSite=None; Secure` if UI and API differ.

Do not put TMDB or DB URLs on Vercel except `VITE_API_URL`.
