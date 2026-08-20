# Vitaphiles — Database Design

PostgreSQL. SQLAlchemy 2 models + Alembic. No `create_all` in production.

Books and movies are **separate tables**. Reviews, lists, and activity are **typed** (`item_kind`: `BOOK` | `MOVIE`) with a check that the matching FK is set.

---

## ER (logical)

```text
users 1──1 profiles
users 1──* refresh_tokens
users 1──* user_books  *──1 books
users 1──* user_movies *──1 movies
users 1──* reviews
users 1──* lists 1──* list_items
users 1──* follows (follower / followee)
users 1──* likes
users 1──* comments
users 1──* activities
users 1──* notifications

books *──* authors     (book_authors)
books *──* genres      (book_genres)
movies *──* genres     (movie_genres)
movies *──* people     (movie_credits: DIRECTOR | CAST)
```

---

## Tables

### `users`

| Column | Type | Notes |
| --- | --- | --- |
| id | PK | |
| email | citext/str unique | login |
| username | str unique | public handle |
| password_hash | str | bcrypt |
| token_version | int | invalidate access JWTs |
| created_at, updated_at | timestamptz | |

### `profiles`

| Column | Notes |
| --- | --- |
| user_id | PK/FK unique |
| display_name, bio, avatar_url | nullable |
| favorite_book_id, favorite_movie_id | optional FKs SET NULL |

### `refresh_tokens`

Hashed token, `expires_at`, `revoked_at`, `replaced_by`, `user_agent`, `ip_address`. Unique `token_hash`.

### `authors`

`id`, `name`, unique `(name)` for seed; later `external_id`.

### `people` (film)

`id`, `name`, `tmdb_id` unique nullable — directors and cast.

### `genres`

`id`, `name`, `slug` unique, `kind` enum `BOOK` | `MOVIE` | `BOTH`.

### `books`

title, subtitle, description, isbn10, isbn13, cover_url, published_on, publisher, page_count, language, `external_source`, `external_id`, `avg_rating` numeric, `rating_count` int. Unique `(external_source, external_id)` where both set.

### `movies`

title, original_title, overview, poster_url, backdrop_url, released_on, runtime_minutes, language, country, `external_source`, `external_id`, `avg_rating`, `rating_count`. Unique `(external_source, external_id)`.

### `book_authors` / `book_genres` / `movie_genres`

Composite PKs. `movie_credits`: `movie_id`, `person_id`, `role` (`DIRECTOR`|`CAST`), `billing_order`.

### `user_books`

Unique `(user_id, book_id)`.  
`status` enum WANT_TO_READ | CURRENTLY_READING | READ | ABANDONED.  
`started_at`, `finished_at`, `progress_pages`, `total_pages`, `rating` (0.5–5, half steps), timestamps.  
Check: rating null or in 0.5..5 and `rating * 2` is integer. Progress ≥ 0.

### `user_movies`

Unique `(user_id, movie_id)`.  
`status` WATCHLIST | WATCHED.  
`watched_on`, `rating`, `rewatch_count` ≥ 0.

### `reviews`

`user_id`, `item_kind`, `book_id`, `movie_id`, `body`, `rating`, `is_spoiler`, timestamps.  
Check: exactly one of book_id/movie_id matches kind. Unique `(user_id, book_id)` / `(user_id, movie_id)` via partial unique indexes.

### `comments`

`review_id`, `user_id`, `body`, timestamps. Cascade review delete.

### `likes`

`user_id`, `review_id` unique pair.

### `lists`

`user_id`, title, description, cover_url, `privacy` PUBLIC | PRIVATE | FOLLOWERS_ONLY.

### `list_items`

`list_id`, `item_kind`, book_id/movie_id, `position` int. Unique `(list_id, position)` not required (gaps allowed); unique item per list via partial indexes.

### `follows`

`follower_id`, `followee_id` unique. Check follower ≠ followee.

### `activities`

`actor_id`, `verb` enum (BOOK_ADDED, BOOK_STARTED, BOOK_FINISHED, BOOK_RATED, BOOK_REVIEWED, MOVIE_WATCHED, MOVIE_RATED, MOVIE_REVIEWED, LIST_CREATED, USER_FOLLOWED), optional FKs, `payload` jsonb, `created_at`. Indexed `(actor_id, created_at desc)` and feed query by followed ids.

### `notifications`

`user_id`, `kind`, `is_read`, `payload` jsonb, `created_at`.

---

## Indexes (high traffic)

- `users(email)`, `users(username)`
- `books(external_source, external_id)`, `movies(...)`
- `user_books(user_id, status)`, `user_movies(user_id, status)`
- `reviews(book_id, created_at)`, `reviews(movie_id, created_at)`
- `activities(created_at)` plus actor
- `follows(followee_id)`, `follows(follower_id)`

## Integrity

- Ratings: `CHECK (rating IS NULL OR (rating >= 0.5 AND rating <= 5 AND (rating * 2) = trunc(rating * 2)))`
- Soft delete: not in v1 (hard delete reviews/lists; users stay).
- Aggregates: `books.avg_rating` / `rating_count` updated in RatingService (materialized on write).

## Why not one `titles` table

Pages vs runtime, authors vs cast, reading progress vs rewatches. A generic table would force nullable nonsense and painful queries. Shared social tables are enough.
