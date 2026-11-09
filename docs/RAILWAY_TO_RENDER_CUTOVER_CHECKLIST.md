# Railway to Render cutover checklist

## Goal

Prepare a safe migration from the existing Railway backend to a Render-hosted FastAPI service without changing the Neon database provider or the Vercel frontend.

## Safety gates

- [ ] Confirm the current Railway service and Neon database are still intact.
- [ ] Confirm no production deploy is being performed as part of this task.
- [ ] Confirm the Render configuration is limited to staging review unless the user explicitly approves production cutover.
- [ ] Confirm no secrets are stored in repo files.
- [ ] Confirm no database migration is run on production.

## Preparation checklist

- [ ] Review `backend/railway.toml` and confirm the current Railway app behavior.
- [ ] Confirm the FastAPI entry point is `backend/app/main.py`.
- [ ] Confirm the module path is `app.main:app` when the working directory is `backend/`.
- [ ] Confirm the backend root directory is `backend` for Render.
- [ ] Confirm the build command is `pip install -r requirements.txt`.
- [ ] Confirm the start command is `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- [ ] Confirm the health check path is `/health`.
- [ ] Confirm the app supports readiness via `/health/ready`.
- [ ] Confirm `DATABASE_URL` points to Neon and not a local or Railway-only value.
- [ ] Confirm `JWT_SECRET_KEY` is set with a strong value.
- [ ] Confirm `GEMINI_API_KEY` is set for the default AI provider.
- [ ] Confirm `AI_PROVIDER=Gemini`.
- [ ] Confirm `AI_MODEL` is set.
- [ ] Confirm `FRONTEND_URL` matches the Vercel production domain.
- [ ] Confirm `CORS_ORIGINS` matches the allowlist in use by the frontend.
- [ ] Confirm `ENABLE_HUGGINGFACE=false` unless explicitly enabled.
- [ ] Confirm `SMOLAGENTS_ENABLED=false` unless explicitly enabled.
- [ ] Confirm `GRADIO_ENABLED=false` unless explicitly enabled.

## Staging validation checklist

- [ ] Create a Render staging web service.
- [ ] Set the backend root directory to `backend`.
- [ ] Add required environment variables manually in the Render dashboard.
- [ ] Validate `/health`.
- [ ] Validate `/health/ready` when the PostgreSQL connection is available.
- [ ] Validate `/docs` loads.
- [ ] Validate auth endpoints.
- [ ] Validate the app can read and write to the Neon database.
- [ ] Validate the frontend can call the backend through the new URL.
- [ ] Compare logs and error rates against the Railway service.

## Production approval checklist

- [ ] User approves production cutover.
- [ ] Render staging checks pass.
- [ ] Vercel production `VITE_API_URL` is updated to the approved Render URL.
- [ ] CORS has been checked against the Vercel production origin.
- [ ] Health checks remain valid.
- [ ] Rollback path is documented and kept available.
- [ ] Railway remains usable during the rollback window.

## Rollback

If the Render deployment fails:

1. Keep the Railway service running.
2. Revert the frontend `VITE_API_URL` to the Railway origin.
3. Re-check auth and data flows.
4. Only then decide whether to continue or restore service.

## Final status

This is a migration-preparation checklist, not an automatic deployment. Production cutover requires explicit approval and staged validation.
