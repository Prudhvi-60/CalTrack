# CalTrack Architecture

CalTrack uses a strict three-tier architecture:

```
React (Vite) → REST API (FastAPI) → PostgreSQL
```

- The frontend talks only to `/api/v1/*`. It never opens PostgreSQL or AI provider URLs.
- JWT access tokens are held in memory on the client. Refresh tokens are HttpOnly cookies. API keys stay in backend environment variables.
- Domain math (macros, remaining, trends, period goal targets) lives in `backend/app/utils/nutrition.py` and nutrition services.
- Vision, chat, and PDF parsing are backend services. Food-photo analysis uses a multimodal LLM for estimated nutrition JSON; labels extract printed values. Chat tools call existing meal/goal/nutrition services after Pydantic validation.

See [requirements-checklist.md](requirements-checklist.md) for the Phase 12 review against the assignment.
