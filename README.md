# NutriAI Monorepo

NutriAI is now a full-stack platform with:

- FastAPI backend (`/backend`) using clean architecture, versioned APIs (`/api/v1`), typed schemas, dependency injection, rate limiting, and structured error handling.
- Next.js App Router frontend (`/frontend`) using TypeScript strict mode, Tailwind design tokens, Clerk auth, and a typed API client.
- Convex data layer (`/convex`) with schema + feature queries/mutations/actions + secured HTTP actions for backend-owned persistence.

## Repository Layout

- `/Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/backend`
- `/Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/frontend`
- `/Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/convex`

## Prerequisites

- Python 3.11+
- Node.js 20+
- npm 10+
- Convex CLI (for deployment/sync)

## 1) Backend Setup (FastAPI)

```bash
cd /Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Update `.env` with provider/API credentials and service URLs:

- `GOOGLE_API_KEY`
- `TOGETHER_API_KEY`
- `GROQ_API_KEY`
- `AFFILIATE_CODE`
- `CONVEX_HTTP_ACTIONS_URL=https://festive-kudu-214.convex.site`
- `CONVEX_BACKEND_SECRET=...`
- Clerk settings (`CLERK_ISSUER`, `CLERK_JWT_PUBLIC_KEY`, `CLERK_AUDIENCE`)

Run backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger docs:

- [http://localhost:8000/docs](http://localhost:8000/docs)

## 2) Frontend Setup (Next.js + Clerk + Tailwind)

```bash
cd /Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/frontend
npm install
cp .env.local.example .env.local
```

Update `.env.local`:

- `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`
- `NEXT_PUBLIC_CONVEX_URL=https://festive-kudu-214.convex.cloud`
- `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=...`
- `CLERK_SECRET_KEY=...`

Run frontend:

```bash
npm run dev
```

Frontend URL:

- [http://localhost:3000](http://localhost:3000)

## 3) Convex Setup

From repo root:

```bash
npm install -g convex
convex login
convex dev
```

Project URLs:

- Cloud URL: [https://festive-kudu-214.convex.cloud](https://festive-kudu-214.convex.cloud)
- HTTP Actions URL: [https://festive-kudu-214.convex.site](https://festive-kudu-214.convex.site)

Set Convex environment variable for backend HTTP action auth:

- `BACKEND_CONVEX_SHARED_SECRET` (in Convex env)

Must match backend:

- `CONVEX_BACKEND_SECRET` (in `backend/.env`)

## Auth and Route Protection

- Clerk middleware lives at `/Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/frontend/src/middleware.ts` using `clerkMiddleware()`.
- Dashboard pages are protected in `/Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/frontend/src/app/(dashboard)/layout.tsx` via `auth()` and redirect.

## API Surface (v1)

Base URL: `http://localhost:8000/api/v1`

Core feature groups:

- `/food-insights`
- `/ingredient-checks`
- `/meal-plans`
- `/recipes`
- `/quizzes`
- `/nutri-chat`
- `/calculators`
- `/articles`
- `/recommendations`
- `/health`

## Testing

Backend tests:

```bash
cd /Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/backend
pytest
```

Frontend checks:

```bash
cd /Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/frontend
npm run typecheck
npm run lint
```

## Observability

- Axiom/OTel setup and query examples: `/Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/docs/observability-axiom.md`

## Notes

- All frontend API requests go through `/Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/frontend/src/lib/api.ts`.
- Convex provider/client setup is in `/Users/Admin/Desktop/Project/nutriaiv2/nutriai/nutriai_main/frontend/src/lib/convex.ts`.
- Legacy Streamlit implementation has been removed from the codebase.
