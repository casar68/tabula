.PHONY: dev-backend dev-frontend test-backend test-frontend lint docker-up docker-down db-migrate db-revision

# ── Development ──────────────────────────────────────────────

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

# ── Testing ──────────────────────────────────────────────────

test-backend:
	cd backend && .venv/bin/python -m pytest -v

test-frontend:
	cd frontend && npx vitest run

test: test-backend test-frontend

# ── Linting ──────────────────────────────────────────────────

lint-backend:
	cd backend && .venv/bin/ruff check .

lint-frontend:
	cd frontend && npm run lint

lint: lint-backend lint-frontend

# ── Docker ───────────────────────────────────────────────────

docker-up:
	docker compose up --build

docker-down:
	docker compose down

# ── Database ─────────────────────────────────────────────────

db-migrate:
	cd backend && alembic upgrade head

db-revision:
	cd backend && alembic revision --autogenerate -m "$(msg)"
