.PHONY: help install dev test clean lint format type-check docker-build docker-up docker-down db-init db-migrate

# Color output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Display this help message
	@echo "$(BLUE)CodeForge AI Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(BLUE)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# ============================================================
# SETUP & INSTALLATION
# ============================================================

install: ## Install all dependencies (frontend + backend)
	@echo "$(BLUE)Installing frontend dependencies...$(NC)"
	cd frontend && npm install
	@echo "$(GREEN)✓ Frontend installed$(NC)"
	@echo ""
	@echo "$(BLUE)Installing backend dependencies...$(NC)"
	cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	@echo "$(GREEN)✓ Backend installed$(NC)"

install-frontend: ## Install frontend dependencies only
	cd frontend && npm install

install-backend: ## Install backend dependencies only
	cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

# ============================================================
# DEVELOPMENT
# ============================================================

dev-frontend: ## Start frontend dev server (http://localhost:3000)
	cd frontend && npm run dev

dev-backend: ## Start backend dev server (http://localhost:8000)
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev: ## Start all services (Docker Compose)
	docker-compose up

dev-stop: ## Stop all Docker services
	docker-compose down

# ============================================================
# CODE QUALITY
# ============================================================

lint: lint-frontend lint-backend ## Run all linters

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint

lint-backend: ## Lint backend code
	cd backend && source venv/bin/activate && flake8 app && black --check app && isort --check-only app

format: format-frontend format-backend ## Format all code

format-frontend: ## Format frontend code
	cd frontend && npm run format

format-backend: ## Format backend code
	cd backend && source venv/bin/activate && black app && isort app

type-check: type-check-frontend type-check-backend ## Type check all code

type-check-frontend: ## Type check frontend code
	cd frontend && npm run type-check

type-check-backend: ## Type check backend code
	cd backend && source venv/bin/activate && mypy app

# ============================================================
# TESTING
# ============================================================

test: test-backend ## Run all tests

test-frontend: ## Run frontend tests
	cd frontend && npm test

test-backend: ## Run backend tests
	cd backend && source venv/bin/activate && pytest

test-backend-cov: ## Run backend tests with coverage
	cd backend && source venv/bin/activate && pytest --cov=app --cov-report=html --cov-report=term

# ============================================================
# DATABASE
# ============================================================

db-init: ## Initialize database (create tables)
	cd backend && source venv/bin/activate && python -m scripts.init_db

db-migrate: ## Create Alembic migration
	@read -p "Enter migration message: " msg; \
	cd backend && source venv/bin/activate && alembic revision --autogenerate -m "$$msg"

db-upgrade: ## Apply Alembic migrations
	cd backend && source venv/bin/activate && alembic upgrade head

db-downgrade: ## Rollback last Alembic migration
	cd backend && source venv/bin/activate && alembic downgrade -1

# ============================================================
# DOCKER
# ============================================================

docker-build: ## Build Docker images
	docker-compose build

docker-up: ## Start all Docker containers
	docker-compose up -d postgres redis
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "  Postgres: localhost:5432"
	@echo "  Redis: localhost:6379"

docker-down: ## Stop and remove all Docker containers
	docker-compose down

docker-logs-backend: ## Show backend logs
	docker-compose logs -f backend

docker-logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

# ============================================================
# UTILITIES
# ============================================================

clean: ## Clean up generated files and caches
	@echo "$(BLUE)Cleaning up...$(NC)"
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	cd frontend && rm -rf .next build dist coverage
	cd backend && rm -rf .pytest_cache .coverage htmlcov
	@echo "$(GREEN)✓ Cleaned$(NC)"

env: ## Copy .env.example to .env
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(GREEN)✓ .env created from .env.example$(NC)"; \
		echo "$(BLUE)Remember to update .env with your local configuration$(NC)"; \
	else \
		echo "$(RED)✗ .env already exists$(NC)"; \
	fi

# ============================================================
# DOCUMENTATION
# ============================================================

docs: ## Open API documentation (requires backend running)
	@echo "Opening API docs at http://localhost:8000/api/docs"
	@command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8000/api/docs || \
	command -v open >/dev/null 2>&1 && open http://localhost:8000/api/docs || \
	echo "Please open http://localhost:8000/api/docs in your browser"

# ============================================================
# DEFAULT
# ============================================================

.DEFAULT_GOAL := help
