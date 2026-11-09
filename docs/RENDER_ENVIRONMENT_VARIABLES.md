# Render environment variables

## Overview

This file lists the environment variables required for the Render-hosted CalTrack backend. The values are configured in the Render dashboard and must not be committed to the repository.

## Required production variables

| Name | Required | Purpose | Notes |
| --- | --- | --- | --- |
| `ENVIRONMENT` | Yes | Deployment mode | Use `production` for Render |
| `DATABASE_URL` | Yes | PostgreSQL connection string | Must point to the existing Neon database |
| `JWT_SECRET_KEY` | Yes | JWT signing secret | Render generates this in `render.yaml`; at least 32 characters |
| `GEMINI_API_KEY` | For AI | Gemini access | Required for AI scan/chat/import; not needed for API startup |
| `AI_PROVIDER` | No | AI provider name | Keep as `Gemini` |
| `AI_MODEL` | No | Gemini model name | Defaults to `gemini-3.1-flash-lite` |
| `FRONTEND_URL` | Yes | Browser origin for the frontend | Use the Vercel production domain |
| `CORS_ORIGINS` | Yes | Allowed browser origins | Match the Vercel deployment domain |

## Optional variables

| Name | Required | Purpose | Default |
| --- | --- | --- | --- |
| `LOG_LEVEL` | No | Log verbosity | `INFO` |
| `AI_TIMEOUT_SECONDS` | No | AI request timeout | `45` |
| `AI_MAX_UPLOAD_BYTES` | No | Max upload size | `5242880` |
| `AI_MIN_CONFIDENCE` | No | Confidence threshold | `0.5` |
| `HUGGINGFACE_API_KEY` | No | Hugging Face token | empty |
| `HUGGINGFACE_MODEL` | No | HF model ID | `google/gemma-2-2b-it` |
| `ENABLE_HUGGINGFACE` | No | Allow HF provider exposure | `false` |
| `SMOLAGENTS_ENABLED` | No | Enable tool-driven agent workflow | `false` |
| `GRADIO_ENABLED` | No | Launch standalone Gradio service | `false` |
| `DB_POOL_SIZE` | No | SQLAlchemy pool size | `5` |
| `DB_MAX_OVERFLOW` | No | Pool overflow | `10` |
| `DB_POOL_TIMEOUT` | No | Connection timeout | `30` |
| `DB_POOL_RECYCLE` | No | Pool recycle window | `1800` |

## Render configuration note

For Render dashboards and `render.yaml`, keep all secrets in the dashboard rather than in version-controlled files. Use `sync: false` for values that are managed outside the repo and should not be committed.
The Render service's Root Directory must be `backend`; this is where `requirements.txt` is located. Render supplies `PORT`, so do not add it as a custom environment variable.

## Security rules

- Do not put secrets in `render.yaml` if they are sensitive values.
- Do not log `DATABASE_URL`, `GEMINI_API_KEY`, or `JWT_SECRET_KEY`.
- Keep optional AI integrations off unless the team explicitly enables them.
- Gemini remains the default provider for the current project.

## Example Render env subset

```text
ENVIRONMENT=production
DATABASE_URL=postgresql://user:password@host:5432/dbname?sslmode=require
JWT_SECRET_KEY=<generated-by-render>
GEMINI_API_KEY=your-key
AI_PROVIDER=Gemini
AI_MODEL=gemini-3.1-flash-lite
FRONTEND_URL=https://your-app.vercel.app
CORS_ORIGINS=https://your-app.vercel.app
ENABLE_HUGGINGFACE=false
SMOLAGENTS_ENABLED=false
GRADIO_ENABLED=false
```

On Vercel, separately set `VITE_API_URL` to the Render public API origin, with no trailing slash or `/api/v1` suffix, and redeploy. Do not copy backend secrets to Vercel.
