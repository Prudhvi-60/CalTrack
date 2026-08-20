# Vitaphiles — Phased Implementation Plan

Work lives in `vitaphiles/`. CalTrack at the repository root is untouched.

## Risks

| Risk | Mitigation |
| --- | --- |
| External APIs rate limits / missing keys | Integrations behind services; seed catalog for demo without keys |
| Cross-origin cookies (SPA vs API) | Local Vite proxy; production SameSite/CORS like CalTrack lessons |
| Dual domains (book vs movie) leaking into one “media” model | Separate tables; typed reviews/lists |
| Scope explosion | Ship one phase per PR; Phase 2 is auth only |

## Dependencies

Phase 2 needs Phase 1 config, DB, CORS.  
Phase 3 needs auth + BookMetadataService.  
Social feed needs activities written from tracking/review services.

## Phase checklist

| Phase | Status | Deliverable |
| --- | --- | --- |
| 1 Foundation | Done | Layout, Docker, FastAPI health, Alembic schema, branded SPA shell |
| 2 Auth | **This PR** | Register/login/refresh/logout/me, protected routes |
| 3 Books | | Search, detail, track, rate, review |
| 4 Movies | | TMDB, watchlist/watched, rate, review |
| 5 Library | | My Books / My Movies filters |
| 6 Social | | Profiles, follow, feed, likes, comments |
| 7 Lists | | CRUD, reorder, privacy |
| 8 Discovery | | Trending, filters, recs v0 |
| 9 Statistics | | Recharts |
| 10 Polish | | A11y, empty/error, motion |
| 11 Testing | | pytest + critical Vitest |
| 12 Deploy | | Railway/Vercel docs + env |

## Phase 1 done when

- `docker compose` in `vitaphiles/` starts Postgres.
- `alembic upgrade head` creates the schema.
- `GET /health` and `GET /health/ready` work.
- Frontend at `:5174` shows branded Home / Discover / Books / Movies / Library shells with empty/loading-ready layout.
- `.env.example` lists secrets; none committed.

## Phase 2 done when

- Register/login return an access JWT and set `vitaphiles_refresh`
- Refresh rotates; reuse is rejected
- `/me` requires a valid Bearer token
- Library / profile routes are client-protected; API still 401s without a token
- pytest covers auth; frontend covers login/register validation

## Explicitly not in Phase 1

Login persistence, TMDB/Google calls, reviews CRUD, feed, recommendations.

## Explicitly not in Phase 2

Live catalog APIs, reviews, follows, lists CRUD.
