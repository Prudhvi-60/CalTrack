# Authentication (Vitaphiles)

## Phase 2 (implemented)

| Endpoint | Notes |
| --- | --- |
| `POST /api/v1/auth/register` | email, username, display_name, password ≥ 8. HttpOnly refresh cookie + access JWT |
| `POST /api/v1/auth/login` | Same cookie + access token |
| `POST /api/v1/auth/refresh` | Reads cookie, **rotates** refresh token, reuse of the old cookie revokes the family |
| `POST /api/v1/auth/logout` | Increments `token_version`, revokes refresh rows, clears cookie |
| `GET /api/v1/auth/me` | Bearer access token |
| `PATCH /api/v1/auth/me` | display_name, bio |
| `POST /api/v1/auth/change-password` | Verifies current password; revokes other sessions |

**Access token:** HS256 JWT, ~15 minutes, claims `sub` / `user_id`, `type=access`, `ver` (token_version). Stored **in memory** on the SPA (`src/api/token.ts`), not localStorage.

**Refresh token:** opaque `secrets.token_urlsafe`, SHA-256 hashed with `JWT_REFRESH_SECRET` as pepper, stored in `refresh_tokens`. Cookie name `vitaphiles_refresh`, path `/api/v1/auth`, HttpOnly, SameSite=Lax, Secure in production.

**Passwords:** bcrypt (72-byte digest cap).

**Rate limit:** sliding window on register/login/refresh (`AUTH_RATE_LIMIT_PER_MINUTE`).

Frontend `ProtectedRoute` is UX only. The API still requires `get_current_user` on private routes.

## Forgot password (architecture, not shipped)

Do not send email until a provider exists. Planned table: `password_reset_tokens` (user_id, token_hash, expires_at, used_at). Endpoint would always return a generic 202 so emails cannot be enumerated.

## Interview talking points

- Why access JWT is short-lived and refresh is rotated
- Why reuse of a revoked refresh token kills the whole session (theft detection)
- Why the browser never sees TMDB/Google keys (unrelated to auth, same “server as security boundary” idea)
