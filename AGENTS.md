# Repository Guidelines

Practical guide for AI assistants working in this repo. Verify against code before large changes; design specs in `docs/superpowers/` are the source of truth for intended architecture.

## Project Overview

**齐家 · 家庭投资助手 (Qijia Family Investment Assistant)** — private, single-family investment ledger + AI analysis assistant. Not multi-tenant: all users share one portfolio dataset by design.

- **Stack**: FastAPI 0.115 (Python 3.11+, async-first) · Next.js 16 (App Router, React 19, TS strict) · PostgreSQL 16 + SQLAlchemy 2.0 + Alembic · Redis 7 (sessions, market cache, APScheduler) · DeepSeek via OpenAI SDK · AKShare + Tencent/Sina/EastMoney market data.
- **Deployment**: single Docker Compose instance — nginx (80) → frontend:3000 / backend:8000. Backend container auto-runs `alembic upgrade head` + `scripts/init_users.py` on start.
- **Features**: dashboard with risk/correlation/sector cards, holdings + transaction CRUD, Excel import, market auto-refresh, AI chat (SSE quick/deep modes), daily morning reports, memos, allocation targets + tax-aware rebalance, push notifications, operation audit log.

## Architecture & Data Flow

### Backend layering (strict, one-directional)

```
api/v1/<resource>.py (thin router)  →  services/<resource>.py (all queries/commits)
    →  models/<resource>.py (pure ORM)  +  schemas/<resource>.py (Pydantic v2)
```

- Routers parse input, call services, return. No business logic or direct DB access in routers — **exceptions**: `api/v1/memos.py`, `settings.py`, `operation_logs.py` query inline (known inconsistency; follow the service pattern for new code).
- Services own SQLAlchemy queries, commit, and write an `OperationLog` row per mutation.
- Request flow: router (body schema `XxxCreate`) → `service.create_xxx(db, data, user.id)` → `db.add()` + `OperationLog` → `commit`/`refresh` → `XxxResponse.model_validate(obj)` (response models use `model_config = {"from_attributes": True}`).

### Auth — cookie + Redis session, NOT JWT

`core/security.py` + `core/deps.py`: bcrypt password hash; login issues `session_id` cookie (httpOnly, samesite=lax, `secure=COOKIE_SECURE`) backed by Redis key `session:<id>` → `user_id`, TTL `SESSION_EXPIRE_HOURS` (168h). Protected routes use `Depends(get_current_user)` which reads the cookie and 401s on missing/expired session. **Never add Bearer headers.** Frontend relies on `credentials: "include"` on all fetches.

### Data isolation — intentional shared holdings

`Holding` has **no `user_id`** — all family members see/edit the same portfolio (product requirement: 家庭共享). `Transaction`, `OperationLog`, `AIConversation`, `Memo` do carry `user_id` for the audit trail. Don't "fix" this without explicit scope; `docs/code-quality-audit-2026-05-20.md` (C1/C3) flags it as a risk — treat as open design tension, not a bug.

### Scheduler (`core/scheduler.py`)

APScheduler `AsyncIOScheduler` started/stopped in the FastAPI `lifespan` (alongside Redis init). Jobs each open their own `async with async_session()`: A-share price refresh during CN trading hours (5-min cron), fund NAV daily 20:00, daily snapshot 15:30, morning AI report 08:00, AI conversation cleanup 03:00.

### Market data (`services/market*.py` — five files, split by concern)

- `market.py` — orchestration; Redis cache `price:<symbol>` (TTL 5min stocks / 24h funds); sync fetchers wrapped in `asyncio.to_thread`.
- `market_sources.py` — HTTP fetchers per source with retry/fallback chain Tencent→Sina→EastMoney.
- `market_parsers.py` — pure response parsers (Decimal-safe).
- `market_symbols.py` — symbol→market logic (`.HK`/`.SH`/`.SZ` suffixes, AKShare 6-digit normalization).
- Persistent `PriceCache` table backs Redis; `fail_count >= 3` → stale flag + warning.

### Frontend

- No Redux/Zustand/React Query — local `useState`/`useEffect` plus `lib/api.ts` (single `api` namespace object with typed `request<T>()` helpers) and `lib/api-cache.ts` (in-memory TTL cache).
- `app/layout.tsx` wraps everything in `components/layout/auth-guard.tsx`: client component calling `api.auth.me()` on path change, redirecting to `/login` on 401.
- **AI SSE streaming bypasses `api.ts`** — `app/ai/page.tsx` uses raw `fetch` + `ReadableStream` reader; the typed wrapper would break streaming. Same for `api.ai.chatUrl` (exposes raw URL).
- TS types mirror backend schemas in `src/types/index.ts`; format via `lib/format.ts` (zh-CN Intl).

## Key Directories

| Path | Purpose |
|---|---|
| `backend/app/api/v1/` | 13 thin routers, registered in `router.py` under `/api/v1` |
| `backend/app/services/` | All business logic + DB access (~17 services) |
| `backend/app/models/` | 11 SQLAlchemy 2.0 declarative models |
| `backend/app/schemas/` | Pydantic v2 request/response models |
| `backend/app/core/` | `config.py` (pydantic-settings), `database.py`, `deps.py`, `security.py`, `scheduler.py`, `time.py` |
| `backend/alembic/versions/` | 6 migrations; head = `c7d8e9f01234_timezone_aware_datetimes` |
| `backend/tests/` | Integration tests (need PG+Redis); `tests/unit/` = pure, no DB |
| `backend/scripts/` | `init_users.py` — idempotent default-user seeder |
| `frontend/src/app/` | App Router pages: `/`, `/login`, `/trade`, `/ai`, `/reports`, `/memos`, `/allocation`, `/history`, `/settings` |
| `frontend/src/components/` | `dashboard/`, `ui/` (shadcn), `holdings/`, `transactions/`, `import/`, `trade/`, `layout/` — tests co-located |
| `frontend/src/lib/` | `api.ts`, `api-cache.ts`, `format.ts`, `asset-type-meta.ts` |
| `frontend/e2e/` | Playwright specs (not in CI) |
| `docker/` | Dockerfiles + `entrypoint-backend.sh` (auto-migrate + seed + uvicorn) |
| `docs/superpowers/` | Design specs + implementation plans (source of truth) |
| `scripts/` | `backup.sh` — pg_dump gzip, 30-day retention, cron 02:00 (Redis not backed up) |

## Development Commands

```bash
# ── Backend (cwd: backend/) ───────────────────────────────────────
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000      # dev server (:8000)
pytest tests/ -v --tb=short                    # all tests (needs PG family_invest_test + Redis)
pytest tests/unit/ -v                          # pure unit tests (no DB)
pytest tests/test_auth.py -v                   # single file
ruff check .                                    # lint (advisory; not in requirements.txt)
alembic upgrade head                            # migrations
python scripts/init_users.py                    # seed default users

# ── Frontend (cwd: frontend/) ─────────────────────────────────────
npm ci
npm run dev                  # next dev (:3000)
npm run build                # next build (standalone)
npm test                     # vitest run
npm run test:watch           # vitest watch
npx vitest run src/lib/api-cache.test.ts   # single file
npm run lint                 # eslint (advisory)
npx tsc --noEmit             # typecheck (BLOCKING in CI)
npm run test:e2e             # playwright (app must be running at baseURL)

# ── Full stack (cwd: repo root) ───────────────────────────────────
cp .env.example .env                             # set POSTGRES_PASSWORD, REDIS_PASSWORD
docker compose build && docker compose up -d     # nginx:80 + frontend + backend + postgres + redis
docker compose logs -f / docker compose down
```

**Backend test env**: conftest derives test DB as `DATABASE_URL` with `/family_invest` → `/family_invest_test`; you must have that Postgres DB and a Redis running. CI provisions them as service containers.

## Code Conventions & Common Patterns

- **Backend naming**: snake_case files/fields, PascalCase classes; schemas as `XxxCreate`/`XxxResponse`. **Frontend naming**: kebab-case files, PascalCase components; imports via `@/` alias → `src/`.
- **SQLAlchemy 2.0 style only**: `Mapped[]` / `mapped_column()`, `class Base(DeclarativeBase)` in `core/database.py`; async engine (`postgresql+asyncpg`), `async_sessionmaker(expire_on_commit=False)`. Money = `Numeric(18,4)`; UUID PKs; timestamps `DateTime(timezone=True)`.
- **Time**: use `core/time.py::utcnow()` — never deprecated `datetime.utcnow()`.
- **Error handling**: no global exception handler; services raise `HTTPException(status_code, detail="中文消息")` directly (401 未登录 / 404 `<resource>不存在` / 400 for business-rule violations). POST create endpoints return 201.
- **Dependency injection**: `db: AsyncSession = Depends(get_db)` + `user: User = Depends(get_current_user)` on protected routes. Tests override `app.dependency_overrides[get_db]`.
- **New model checklist**: create model → ensure imported via `app/models` (Alembic `env.py` needs it on `Base.metadata` for autogen) → write Alembic revision → schema in `schemas/` → service + router.
- **Frontend components**: shadcn/ui primitives in `components/ui/`; per-card `ErrorBoundary`; `credentials: "include"` on every API call; custom `ApiError` class.
- **SSE contract**: backend streams `data: {content}\n\n` lines ending with disclaimer + `{done:true}`; deep mode emits `{progress}` events.

## Important Files

- `backend/app/main.py` — app factory + lifespan (Redis init, scheduler start/stop); only `/health` outside `/api/v1`.
- `backend/app/api/v1/router.py` — all v1 route registration.
- `backend/app/core/config.py` — `pydantic-settings` singleton; reads repo-root `.env` **then** `backend/.env`; `extra="ignore"`; production validator rejects weak DB passwords.
- `backend/app/core/deps.py` / `security.py` — session auth implementation.
- `backend/alembic/env.py` — async migrations; URL from `settings.DATABASE_URL` (ini URL is a placeholder).
- `frontend/src/lib/api.ts` — typed API namespace; base = `NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"`.
- `frontend/src/components/layout/auth-guard.tsx` — client-side auth gate wrapping all pages.
- `frontend/next.config.ts` — only `output: "standalone"`; no rewrites/proxy (frontend calls backend absolutely; CORS handles dev).
- `docker/entrypoint-backend.sh` — migrate + seed + uvicorn on container start.
- `.github/workflows/ci.yml` — canonical verification commands.

## Runtime/Tooling Preferences

- **Python**: 3.11+ (Docker image `python:3.11-slim`; CI uses 3.12). No `pyproject.toml` — deps pinned exactly in `backend/requirements.txt`; ruff installed ad-hoc (`pip install ruff`), version ~0.15.x.
- **Node**: 20 (CI + Docker). Package manager: **npm** (`npm ci`, `package-lock.json` committed). No pnpm/yarn/bun.
- **Blocking CI gates**: `tsc --noEmit`, backend `pytest`, frontend `vitest run`, `next build`, Docker builds. **Non-blocking (advisory)**: `ruff check . --exit-zero`, `eslint … || true`. Don't rely on lint to catch issues.
- **PostgreSQL + Redis are hard requirements** — no SQLite fallback anywhere (sessions, market cache, and scheduler all need Redis; CI uses real service containers, not mocks).
- **`NEXT_PUBLIC_API_URL` is baked at build time** — changing `NGINX_HOST_PORT` after a frontend image build requires `docker compose build frontend`.
- **Env vars**: `APP_ENV`, `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`, `SESSION_EXPIRE_HOURS`, `COOKIE_SECURE`, `DEEPSEEK_API_KEY/BASE_URL/MODEL`, `DEEPSEEK_VENDOR_*` (vendor overrides official), `AI_DAILY_LIMIT`, `AI_DEEP_MAX_TOKENS`; compose-level `POSTGRES_*`, `REDIS_PASSWORD`, `NGINX_HOST_PORT`. Note: `SECRET_KEY` appears in docs/CI env but has **no consumer in backend code** (sessions use random Redis-backed IDs) — vestigial.

## Testing & QA

- **Backend**: pytest 8.3 + pytest-asyncio 0.24, **no pytest config file → strict asyncio mode**: every async test needs explicit `@pytest.mark.asyncio`. Client is always async `httpx.AsyncClient` over `ASGITransport` (never sync `TestClient`; note ASGITransport does NOT trigger lifespan — conftest's `ensure_redis` fixture compensates). Autouse `setup_database` does `create_all`/`drop_all` **per test** (schema from models, not migrations). Key fixtures: `db_session`, `test_user` (testuser/testpass), `client`, `authenticated_client` (logged-in cookie client). No factories — inline payloads via HTTP or direct ORM construction.
- **Backend test layout**: top-level = integration (DB+HTTP); `tests/unit/` = pure service-function tests (e.g. `_pearson_corr`, `_compute_trade_costs` fee tiers) with no fixtures. Scheduler tests assert on cron-trigger constants, not a running scheduler.
- **Frontend unit**: Vitest 4 + jsdom + `@testing-library/react`; `globals: true`, setup imports `@testing-library/jest-dom/vitest`. Universal mock pattern: `vi.mock("@/lib/api", () => ({ api: { <ns>: { <method>: vi.fn() } } }))` then `vi.mocked(...)` per-test; assert with `screen.findByText` for async data. Tests co-located with source.
- **E2E**: Playwright, chromium only, `workers: 1`, `fullyParallel: false`. **No `webServer` block** — the app must already be running at `PLAYWRIGHT_BASE_URL ?? "http://localhost:8888"` (nginx port, not `next dev` :3000). `e2e/app.spec.ts` covers auth redirect, admin login + all 8 routes, nav flow, phase-2 dashboard/import flows. Not run in CI.
- **Coverage**: no thresholds or coverage tooling configured on either side — CI passes on green tests alone.

## Known Pitfalls (from `docs/code-quality-audit-2026-05-20.md` — verify before regressing)

- Market service uses sync `requests.get()` in places (only partially wrapped in `asyncio.to_thread`) and has serial per-symbol refresh (N+1) — prefer `httpx.AsyncClient` + batching when touching `market.py`.
- `SECRET_KEY`/`backend/.env` hygiene: never commit real secrets; `.gitignore` covers env files.
- Single-branch `main` development; design specs (`docs/superpowers/specs/`) are confirmed — avoid scope creep. Out of scope unless explicitly approved: multi-tenant, model switching beyond DeepSeek, overseas markets, native/PWA mobile (open P2 issues #8–#11).
