.PHONY: help install setup up down logs test clean migrate build

# Load environment variables from .env file
-include .env
export

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install Python dependencies
	uv sync
	uv run playwright install chromium

dev: ## Run bot locally (not in Docker)
	uv run python -m src.main

up: ## Start all services with Docker Compose
	docker-compose up -d

down: ## Stop all services
	docker-compose down

clean: ## Stop services and remove volumes
	docker-compose down -v

logs-all: ## View all service logs
	docker-compose logs -f

build: ## Build Docker image
	docker-compose build

rebuild: ## Rebuild and restart bot
	docker-compose up -d --build bot


db-shell: ## Access PostgreSQL shell
	docker-compose exec postgres psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
