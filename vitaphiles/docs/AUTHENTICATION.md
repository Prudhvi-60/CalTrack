# Authentication (Vitaphiles)

**Phase 1:** not implemented (guest-visible shell only).

**Target (Phase 2):**

- `POST /api/v1/auth/register` `login` `refresh` `logout`
- `GET/PATCH /api/v1/auth/me`
- `POST /api/v1/auth/change-password`
- Access JWT in memory (~15 min)
- Refresh: HttpOnly cookie, SHA-256 in `refresh_tokens`, rotation
- bcrypt passwords
- Frontend `ProtectedRoute` is UX only; API enforces `get_current_user`

Forgot-password: schema/token table can be added later; do not fake email send in v1 without a provider.
