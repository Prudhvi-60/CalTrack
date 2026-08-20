# API (Vitaphiles)

Version prefix: `/api/v1`.

**Phase 1:** `GET /`, `GET /health`, `GET /health/ready`, `GET /health/db`.

Later: `/auth`, `/users`, `/books`, `/movies`, `/reviews`, `/library`, `/lists`, `/follows`, `/activity`, `/notifications`, `/recommendations`, `/search`, `/stats`.

Errors:

```json
{ "error": { "code": "RESOURCE_NOT_FOUND", "message": "Book not found" } }
```

No stack traces in responses. OpenAPI: `/docs`.
