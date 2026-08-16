# CalTrack

CalTrack is a personal calorie tracker. You log what you eat, set daily nutrition goals, and see how you are doing over time — including photos of food, a nutrition chat, and PDF food-diary import.

This project follows the **Typeface India Software Engineer project assignment**: a full-stack app with a website (frontend) that talks to a separate API (backend), which stores data in a database.

**AI numbers are estimates.** Review them before you save. Nothing from a photo or PDF is stored until you confirm.

---

## Demo video

Watch a short walkthrough of CalTrack: [docs/demo/Demo_Video.mp4](docs/demo/Demo_Video.mp4)

---

## Try it (no setup)

| What | Link |
| --- | --- |
| **Website (sign in)** | [https://frontend-production-15c16.up.railway.app/login](https://frontend-production-15c16.up.railway.app/login) |
| **Website (home)** | [https://frontend-production-15c16.up.railway.app](https://frontend-production-15c16.up.railway.app) |
| **API documentation** | [https://caltrack-production-c5cd.up.railway.app/docs](https://caltrack-production-c5cd.up.railway.app/docs) |
| **API health** | [https://caltrack-production-c5cd.up.railway.app/health](https://caltrack-production-c5cd.up.railway.app/health) |

1. Open the website and **create an account** (Register), then sign in.
2. Set goals, log a meal, open Reports, try **AI Scan**, **Chat**, or **Import**.
3. Open the API docs if you want to see the same features as technical endpoints.

Your meals and goals belong only to your account. Other people cannot see them.

---

## What you can do

| In the assignment | In CalTrack |
| --- | --- |
| Set health goals | Daily calories, protein, carbs, fat, optional weight goal |
| Log meals | Breakfast, lunch, dinner, snacks — food name, quantity, calories, macros, micros |
| List food over a time range | Meals page: filter by date, date range, meal type, search; pages of results |
| Nutrition reports and graphs | Dashboard + Reports: calorie trend, macros, micronutrients, goal vs actual |
| AI from a photo | AI Scan: plate or nutrition label → review → save |
| Chat (bonus) | Ask in plain English to log meals, check remaining calories, or get summaries |
| Several users (bonus) | Sign up / log in; each person has private data |
| Import a PDF (bonus) | Upload a food diary or meal-plan PDF, review, then save |

The website never talks to the database or to Google Gemini directly. It only calls the CalTrack API.

---

## How to use the website

1. **Register** with your name, email, and password, then **sign in**.
2. **Goals** — set a daily calorie target and macro targets.
3. **Log meal** — add foods by hand, or use **AI Scan** / **Import**.
4. **Dashboard** — today vs your goals.
5. **Meals** — history, filters, edit, delete.
6. **Reports** — 7 / 30 / 90 day charts.
7. **Chat** — text only. Photos go to AI Scan.
8. **Settings** — name, password, optional training opt-in, sign out.

---

## Run it on your computer

You need: **Git**, **Python 3.12+**, **Node 20+**, and **PostgreSQL** (or Docker).

```bash
git clone https://github.com/Prudhvi-60/CalTrack.git
cd CalTrack
```

**Windows**

```bash
copy .env.example .env
copy frontend\.env.example frontend\.env
```

**macOS / Linux**

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env
```

Leave `VITE_API_URL` empty locally so the website uses the built-in `/api` proxy (same-site cookies work).

**Database + API**

```bash
docker compose up postgres -d
cd backend
python -m venv .venv
```

Windows: `.venv\Scripts\activate`  
macOS / Linux: `source .venv/bin/activate`

```bash
pip install -r requirements.txt
alembic upgrade head
python -m scripts.seed
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

**Website** (another terminal)

```bash
cd frontend
npm install
npm run dev
```

| Local | URL |
| --- | --- |
| Website | [http://localhost:5173](http://localhost:5173) |
| API docs | [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) |
| Health | [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health) |

Local demo user (created by `python -m scripts.seed` — **not** for the public Railway site):

- Email: `demo@caltrack.app`
- Password: `DemoPass123!`

Optional: `docker compose up --build` runs the full stack.

### Tests

```bash
cd backend
pytest
cd ../frontend
npm test
npm run build
```

---

## How it is built (short)

```
Your browser  →  CalTrack website  →  CalTrack API  →  PostgreSQL
                                      ↓
                                 Gemini (photos, chat, PDF)
```

| Layer | Technology |
| --- | --- |
| Website | React + Vite + TypeScript |
| API | FastAPI (Python) |
| Database | PostgreSQL (Alembic migrations) |
| AI | Google Gemini, called only from the API |

Sign-in uses the API (JWT in memory + HttpOnly refresh cookie). This is **not** a switch to a third-party login product.

More detail: [docs/architecture.md](docs/architecture.md) · [docs/requirements-checklist.md](docs/requirements-checklist.md) · [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## Assumptions

- Nutrition from photos and chat is **estimated**, not lab-accurate. You confirm before save (chat tools that log a meal are validated on the server, then saved).
- Days in reports use **UTC** calendar dates, not your phone’s local timezone.
- Micronutrients are whatever you (or AI) enter; they are not a complete lab panel.
- PDF import works best with a readable diary or meal plan. Scanned or messy PDFs may need edits on the review screen.
- Chat is **text**. Food photos belong on AI Scan.
- Production secrets (`DATABASE_URL`, `JWT_SECRET_KEY`, `GEMINI_API_KEY`) stay on the API host only — never in the website.
- If AI is not configured, scan/chat/import return a clear error instead of crashing.
- Local demo login is only after seeding your own database. Register on the live site.

---

## If something goes wrong

| Problem | What to try |
| --- | --- |
| Live site will not sign in | Register a new account; confirm you are on the Railway website URL above |
| API docs open, website cannot load data | The website must be allowed in the API CORS / `FRONTEND_URL` settings |
| Photo analysis fails | JPEG, PNG, or WebP, under 5 MB; Gemini must be configured on the API |
| Local login works then drops | Keep `VITE_API_URL` empty so the Vite proxy is used |

Do not commit `.env` files or API keys.
