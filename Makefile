.PHONY: help up down restart logs logs-app logs-db ps shell shell-db build clean test setup-db ingest stop-app start-app

# Default target
help:
	@echo "SoundHash Docker Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make up          - Start all services (db + app)"
	@echo "  make down        - Stop and remove all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - View logs from all services"
	@echo "  make logs-app    - View logs from app service"
	@echo "  make logs-db     - View logs from db service"
	@echo "  make ps          - List running containers"
	@echo "  make shell       - Open bash shell in app container"
	@echo "  make shell-db    - Open psql shell in db container"
	@echo "  make build       - Build Docker images"
	@echo "  make clean       - Stop services and remove volumes"
	@echo "  make test        - Run tests in container"
	@echo "  make setup-db    - Initialize database schema"
	@echo "  make ingest      - Run ingestion script (dry-run with 5 videos)"
	@echo "  make stop-app    - Stop only the app service"
	@echo "  make start-app   - Start only the app service"

# Start all services
up:
	docker compose up -d

# Stop all services
down:
	docker compose down

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

# Run tests in container
test:
	docker compose exec app pytest -v

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
