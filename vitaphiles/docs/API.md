# API (Vitaphiles)

Version prefix: `/api/v1`.

**Phase 2:** `POST /api/v1/auth/register` `login` `refresh` `logout` `change-password`; `GET/PATCH /api/v1/auth/me`.

**Phase 1:** `GET /health`, `GET /health/ready` (also under `/api/v1`).

Later: `/auth`, `/users`, `/books`, `/movies`, `/reviews`, `/library`, `/lists`, `/follows`, `/activity`, `/notifications`, `/recommendations`, `/search`, `/stats`.

Errors:

```json
{ "error": { "code": "RESOURCE_NOT_FOUND", "message": "Book not found" } }
```

No stack traces in responses. OpenAPI: `/docs`.
