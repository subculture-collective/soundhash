.PHONY: help setup lint type test format format-fix docker-up docker-down
.PHONY: up down restart logs logs-app logs-db ps shell shell-db build clean setup-db ingest stop-app start-app

# Python executable - use virtual environment if activated, otherwise use system python
PYTHON := python3
PYTEST := pytest
RUFF := ruff
BLACK := black
MYPY := mypy

# Directories to lint/format
LINT_DIRS := src scripts config

# Default target
help:
	@echo "SoundHash Makefile - Development & Docker Commands"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make setup       - Set up local development environment"
	@echo "  make test        - Run tests locally"
	@echo "  make lint        - Run all linters"
	@echo ""
	@echo "🔧 Local Development:"
	@echo "  make setup       - Create venv and install dependencies"
	@echo "  make lint        - Run ruff linter"
	@echo "  make type        - Run mypy type checker"
	@echo "  make test        - Run pytest tests locally"
	@echo "  make format      - Check code formatting (black)"
	@echo "  make format-fix  - Auto-fix code formatting"
	@echo ""
	@echo "🐳 Docker Commands:"
	@echo "  make docker-up   - Start all services (db + app)"
	@echo "  make docker-down - Stop and remove all services"
	@echo "  make up          - Alias for docker-up"
	@echo "  make down        - Alias for docker-down"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make logs-app    - View logs from app service"
	@echo "  make logs-db     - View logs from db service"
	@echo "  make ps          - List running containers"
	@echo "  make shell       - Open bash shell in app container"
	@echo "  make shell-db    - Open psql shell in db container"
	@echo "  make build       - Build Docker images"
	@echo "  make clean       - Stop services and remove volumes (⚠️  destroys data)"
	@echo "  make setup-db    - Initialize database schema"
	@echo "  make ingest      - Run ingestion script (dry-run with 5 videos)"
	@echo "  make stop-app    - Stop only the app service"
	@echo "  make start-app   - Start only the app service"
	@echo ""
	@echo "💡 Tips:"
	@echo "  - Run 'make setup' first for local development"
	@echo "  - Use 'make lint type test' before committing"
	@echo "  - CI runs these same targets for consistency"

# ============================================================================
# Local Development Targets
# ============================================================================

# Set up local development environment
setup:
	@echo "🔧 Setting up local development environment..."
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		$(PYTHON) -m venv .venv; \
	fi
	@echo "Installing dependencies..."
	@. .venv/bin/activate && pip install -q --upgrade pip
	@. .venv/bin/activate && pip install -q -r requirements-dev.txt
	@. .venv/bin/activate && pip install -q -r requirements.txt
	@echo "✅ Setup complete! Activate venv with: source .venv/bin/activate"

# Run linter (ruff)
lint:
	@echo "🔍 Running ruff linter..."
	@$(RUFF) check $(LINT_DIRS)

# Run type checker (mypy)
type:
	@echo "🔍 Running mypy type checker..."
	@$(MYPY) src scripts || true

# Run tests locally
test:
	@echo "🧪 Running tests..."
	@$(PYTEST) -q

# Check code formatting
format:
	@echo "🎨 Checking code formatting..."
	@$(BLACK) --check $(LINT_DIRS)

# Auto-fix code formatting
format-fix:
	@echo "🎨 Auto-fixing code formatting..."
	@$(BLACK) $(LINT_DIRS)

# ============================================================================
# Docker Targets
# ============================================================================

# Start all services (primary docker command)
docker-up:
	docker compose up -d

# Stop all services (primary docker command)
docker-down:
	docker compose down

# Aliases for docker commands (for backward compatibility)
up: docker-up

down: docker-down

# Restart all services
restart:
	docker compose restart

# View logs from all services
logs:
	docker compose logs -f

# View logs from app service
logs-app:
	docker compose logs -f app

# View logs from db service
logs-db:
	docker compose logs -f db

# List running containers
ps:
	docker compose ps

# Open bash shell in app container
shell:
	docker compose exec app bash

# Open psql shell in db container
shell-db:
	docker compose exec db psql -U $${DATABASE_USER:-soundhash_user} -d $${DATABASE_NAME:-soundhash}

# Build Docker images
build:
	docker compose build

# Stop services and remove volumes (WARNING: destroys data)
clean:
	docker compose down -v
	rm -rf logs/* temp/*

# Initialize database schema using Alembic
setup-db:
	docker compose exec app python scripts/setup_database.py

# Run ingestion script with safe defaults
ingest:
	docker compose exec app python scripts/ingest_channels.py --dry-run --max-videos 5

# Stop only the app service
stop-app:
	docker compose stop app

# Start only the app service
start-app:
	docker compose start app
