# Vitaphiles — Product Requirements

**Product:** Vitaphiles  
**Tagline:** Stories worth remembering.  
**Vision:** A unified book + movie discovery, tracking, reviewing, and recommendation platform — inspired by Goodreads and Letterboxd, with its own editorial identity.

CalTrack remains a separate application in this repository. Vitaphiles lives under `vitaphiles/` so existing CalTrack code is not overwritten.

---

## 1. Problem

People who love stories split their cultural life across apps: books in one place, films in another, social discovery in a third. Vitaphiles is one home for **discover → track → experience → review → share**.

## 2. Who it is for

Readers and cinephiles who want a quiet, magazine-like space — not a dashboard, not a generic CRUD admin.

## 3. Product loop

1. Discover a title (search, trending, recommendations, people you follow).
2. Save it (want to read / watchlist).
3. Experience it (currently reading / watched).
4. Rate and optionally review (0.5–5 stars, spoiler flag).
5. Share via activity feed, lists, and profile.
6. Discover the next title.

## 4. Scope by domain

### Books (distinct)

Statuses: `WANT_TO_READ`, `CURRENTLY_READING`, `READ`, `ABANDONED`.  
Progress: optional page counts. Authors, page count, ISBN, publisher.

### Movies (distinct)

Statuses: `WATCHLIST`, `WATCHED`.  
Runtime, directors, cast, backdrop, rewatch count. Rewatch history is a later extension (`user_movie_watches`).

### Shared (only where it is real)

Ratings, reviews, genres, lists, activity, follows, likes, comments, recommendations as a *service*, not a fake “MediaItem” table.

## 5. Functional requirements (MVP through polish)

| Area | Must have | Later |
| --- | --- | --- |
| Auth | Register, login, logout, refresh, me, change password | Email verify, forgot-password send |
| Books | Search/detail via Google Books or Open Library (server-only), track, rate, review | ISBN barcode |
| Movies | Search/detail via TMDB (server-only), watchlist/watched, rate, review | TV shows |
| Library | Tabs for books/movies/reviews/lists | Import from CSV |
| Social | Profile, follow, feed, like, comment | DMs |
| Lists | CRUD, order, PUBLIC/PRIVATE/FOLLOWERS_ONLY | Collaborative lists |
| Discovery | Search, filters, trending/popular/highly rated | Full-text search engine |
| Stats | Year counts, average rating, genre mix, Recharts | Streaks, wrapped |
| Recs | Rule-based RecommendationService | ML ranker |

## 6. Non-functional

- JWT access in memory; HttpOnly refresh cookie; bcrypt; CORS allowlist; no secrets in `VITE_*`.
- Pagination on feeds, search, reviews.
- Mobile bottom nav; desktop editorial nav.
- Accessible forms, focus, alt text, spoiler reveal is a user action.

## 7. Out of scope for v1

Microservices, Redis, Celery, Elasticsearch, object storage CDN pipeline, ML recommendations, TV series, ebook reader, streaming playback.

## 8. Success for interviews

A reviewer can open the app and immediately understand: *this is for people who love books and movies*. The codebase can be walked: architecture, schema, auth, integrations, authorization, recs, deploy tradeoffs.
