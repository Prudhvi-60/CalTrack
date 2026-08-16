# CalTrack requirements matrix (pre-submission audit)

Statuses: **PASS** only when verified in code and tests (and live API where noted). **PARTIAL** means implemented with a documented gap. **FAIL** means missing or broken.

## CORE REQUIREMENTS

| Requirement | Implementation | API | Frontend | Database | Test | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Goal setting | `GoalService`, `Goals.tsx` | `POST/GET/PUT/DELETE /api/v1/goals` | `/goals` | `goals` | `test_goals.py`, `Goals.test.tsx` | PASS |
| Meal entry | `MealService`, `MealForm` | `POST/GET/PUT/DELETE /api/v1/meals` | `/meals`, `/meals/new`, `/meals/:id` | `meals`, `food_entries` | `test_meals.py`, `NewMeal.test.tsx` | PASS |
| Food item nutrition | Nested food payloads + totals | Meal schemas include macros/micros | `MealForm`, meal details | `food_entries`, `micronutrients` | `test_meals.py`, `test_nutrition.py` | PASS |
| Date / date-range filtering | `MealService.list_meals` | `?date`, `?start_date&end_date` | Meals filter form | `ix_meals_user_id_consumed_at` | `test_meals.py`, `Meals.test.tsx` | PASS |
| Meal-type filtering | Same | `?meal_type=` | Meals type select | `ix_meals_user_id_meal_type` | `test_meals.py`, `Meals.test.tsx` | PASS |
| Pagination for list APIs | `paginated()` | meals, goals, trends, micronutrients | Meals/Goals page controls | n/a | backend list tests | PASS |
| Weekly calorie trends | `NutritionService.weekly` / `trends` | `GET /nutrition/weekly`, `/nutrition/trends` | Dashboard + Reports line charts | meals/food_entries | `test_nutrition_api.py`, `Reports.test.tsx` | PASS |
| Macronutrient reports | Daily/weekly/trends + charts | `/nutrition/daily`, `/weekly`, `/trends` | Macro bar, pie, and daily macro trend | same | nutrition tests + Reports Vitest | PASS |
| Micronutrient summaries | `NutritionService.micronutrients` | `GET /nutrition/micronutrients` | `MicronutrientPanel` | `micronutrients` | `test_nutrition.py`, `test_nutrition_api.py` | PASS |
| Goal vs actual | `NutritionService.goal_comparison` | `GET /nutrition/goal-comparison` | Dashboard + Reports | `goals` + meals | `test_nutrition_api.py` | PASS |
| AI image nutrition extraction | `VisionService`, `analyze_image` | `POST /api/v1/ai/analyze-food` | `/ai-scan` review then `POST /meals` | not written until confirm | `test_ai.py`, `test_ai_parsing.py`, `AIScanner.test.tsx` | PASS |
| Persistent PostgreSQL | SQLAlchemy + Alembic | all CRUD | Axios only | `0001_initial` | `test_database.py`, `test_health.py` | PASS |
| Frontend/backend API separation | `apiClient` Axios | `/api/v1/*` | no DB libraries | n/a | grep: no postgres/sqlalchemy in frontend | PASS |

Daily/weekly/goal-comparison are snapshot endpoints (not item lists). List endpoints that return collections are paginated.

## BONUS REQUIREMENTS

| Requirement | Implementation | API | Frontend | Database | Test | Status |
| --- | --- | --- | --- | --- | --- | --- |
| Conversational AI | `ChatService` + validated tools | `POST /api/v1/chat` | `/chat` | meals/goals via tools | `test_chat.py`, `Chat.test.tsx` | PASS |
| Multi-user support | JWT + owner filters | all protected routes | login/register/settings | `users.user_id` FKs | isolation tests in auth/meals/goals/nutrition | PASS |
| PDF food diary import | text/OCR + Gemini meal-plan extract, table PDF still supported | `POST /api/v1/import/meal-plan`, `/confirm`; `POST /api/v1/import/pdf`, `/confirm` | `/import` | meals on confirm only | `test_pdf.py`, `test_meal_plan.py`, `PdfImport.test.tsx` | PASS |

Chat write tools persist after backend validation (no extra review screen). Scanner still requires explicit confirm.

## Architecture

| Requirement | Status | Evidence |
| --- | --- | --- |
| React → REST → FastAPI → PostgreSQL | PASS | Axios `/api/v1`; FastAPI; SQLAlchemy |
| Frontend never connects to PostgreSQL | PASS | No database usage under `frontend/src` |
| AI only from backend | PASS | `VisionService`, `ChatService` |
| No API keys in frontend | PASS | Only `VITE_API_BASE_URL` |

## Auth and security

| Requirement | Status | Evidence |
| --- | --- | --- |
| Register / login / logout / me | PASS | `test_auth.py` |
| bcrypt hashing, JWT | PASS | `app/core/security.py` |
| Duplicate email, invalid password | PASS | `test_auth.py` |
| Invalid and expired tokens | PASS | `test_auth.py` |
| Cross-user meal/goal/nutrition IDOR | PASS | 404 for other user's IDs |
| `.env` gitignored; `.env.example` present | PASS | `.gitignore`; `.env` not tracked |
| No stack traces in API errors | PASS | `INTERNAL_ERROR` handler in `main.py` |

## Documented gaps

1. Spec listed `users.py`. Profile is `GET/PATCH /api/v1/auth/me` instead.
2. Chat write tools persist after validation (no extra review UI).
3. Hand-built PDF bytes do not extract a clean table; confirm is tested with a parsed table fixture.
4. `JWT_SECRET_KEY` has a development default if `.env` is missing (startup warning added).
5. Vite JS bundle exceeds 500 kB (warning only).
6. Docker frontend image runs `npm run dev`, not a static production build. Compose sets `VITE_API_BASE_URL=http://localhost:8000` so the browser talks to the published backend port.
7. Nutrition windows use UTC calendar days, not the viewer's local timezone.
8. Logout is stateless JWT (client discards the token); the server does not maintain a denylist.
