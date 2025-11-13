.PHONY: help build up down restart logs shell test clean status

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)🌺 Shoghi Platform - Docker Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Quick Start: make up$(NC)"
	@echo ""

build: ## Build the Docker image
	@echo "$(BLUE)Building Shoghi Docker image...$(NC)"
	docker-compose build
	@echo "$(GREEN)✓ Build complete$(NC)"

up: ## Start all services (detached mode)
	@echo "$(BLUE)Starting Shoghi Platform...$(NC)"
	docker-compose up -d
	@sleep 5
	@echo "$(GREEN)✓ Shoghi is running!$(NC)"
	@echo "$(YELLOW)Access at: http://localhost:5000$(NC)"

start: up ## Alias for 'up'

down: ## Stop all services
	@echo "$(BLUE)Stopping Shoghi Platform...$(NC)"
	docker-compose down
	@echo "$(GREEN)✓ Stopped$(NC)"

stop: down ## Alias for 'down'

restart: ## Restart all services
	@echo "$(BLUE)Restarting Shoghi Platform...$(NC)"
	docker-compose restart
	@echo "$(GREEN)✓ Restarted$(NC)"

logs: ## Show logs (follow mode)
	@echo "$(BLUE)Showing logs (Ctrl+C to exit)...$(NC)"
	docker-compose logs -f

logs-tail: ## Show last 100 log lines
	docker-compose logs --tail=100

shell: ## Open bash shell in container
	@echo "$(BLUE)Opening shell in Shoghi container...$(NC)"
	docker-compose exec shoghi bash

python: ## Open Python shell in container
	docker-compose exec shoghi python3

test: ## Run test suite
	@echo "$(BLUE)Running test suite...$(NC)"
	docker-compose exec shoghi pytest -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-quick: ## Run tests (quick mode, no verbose)
	docker-compose exec shoghi pytest --tb=short

status: ## Show container status
	@echo "$(BLUE)Container Status:$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(BLUE)Resource Usage:$(NC)"
	@docker stats shoghi-platform --no-stream

health: ## Check health status
	@docker inspect --format='Health: {{.State.Health.Status}}' shoghi-platform

clean: ## Remove containers and volumes
	@echo "$(RED)⚠️  This will remove all containers and volumes!$(NC)"
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]
	docker-compose down -v
	@echo "$(GREEN)✓ Cleaned$(NC)"

rebuild: ## Rebuild from scratch
	@echo "$(BLUE)Rebuilding from scratch...$(NC)"
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "$(GREEN)✓ Rebuild complete$(NC)"

update: ## Pull latest code and restart
	@echo "$(BLUE)Updating Shoghi...$(NC)"
	git pull origin main
	docker-compose down
	docker-compose build
	docker-compose up -d
	@echo "$(GREEN)✓ Updated and restarted$(NC)"

backup: ## Backup database and data
	@echo "$(BLUE)Creating backup...$(NC)"
	@mkdir -p backups
	@docker cp shoghi-platform:/app/shoghi_grants.db backups/shoghi_grants_$(shell date +%Y%m%d_%H%M%S).db
	@docker cp shoghi-platform:/app/data backups/data_$(shell date +%Y%m%d_%H%M%S) 2>/dev/null || true
	@echo "$(GREEN)✓ Backup saved to backups/$(NC)"

restore: ## Restore database from backup (use BACKUP=filename)
	@if [ -z "$(BACKUP)" ]; then \
		echo "$(RED)Usage: make restore BACKUP=backups/shoghi_grants_20241113.db$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Restoring from $(BACKUP)...$(NC)"
	docker cp $(BACKUP) shoghi-platform:/app/shoghi_grants.db
	docker-compose restart
	@echo "$(GREEN)✓ Restored$(NC)"

install: build up ## Full installation (build + start)
	@echo "$(GREEN)✓ Shoghi Platform installed and running!$(NC)"
	@echo "$(YELLOW)Access at: http://localhost:5000$(NC)"

uninstall: clean ## Complete uninstall
	@echo "$(GREEN)✓ Shoghi Platform uninstalled$(NC)"

dev: ## Start in development mode with live logs
	docker-compose up

prod: ## Start in production mode (optimized)
	@echo "$(BLUE)Starting in production mode...$(NC)"
	FLASK_ENV=production docker-compose up -d
	@echo "$(GREEN)✓ Running in production mode$(NC)"

scale: ## Scale to multiple instances (use INSTANCES=3)
	@if [ -z "$(INSTANCES)" ]; then \
		echo "$(RED)Usage: make scale INSTANCES=3$(NC)"; \
		exit 1; \
	fi
	docker-compose up -d --scale shoghi=$(INSTANCES)
	@echo "$(GREEN)✓ Scaled to $(INSTANCES) instances$(NC)"

stats: ## Show detailed resource statistics
	docker stats shoghi-platform

network: ## Show network information
	@docker network inspect shoghi_shoghi-network

volumes: ## List volumes
	@docker volume ls | grep shoghi

open: ## Open web UI in browser
	@command -v xdg-open > /dev/null && xdg-open http://localhost:5000 || \
	 command -v open > /dev/null && open http://localhost:5000 || \
	 echo "$(YELLOW)Open http://localhost:5000 in your browser$(NC)"

demo: up ## Run demo scenario
	@sleep 5
	@echo "$(BLUE)Running demo...$(NC)"
	docker-compose exec shoghi python3 demo_shoghi.py

version: ## Show version information
	@echo "$(BLUE)Shoghi Platform Version Information:$(NC)"
	@docker-compose exec shoghi python3 --version
	@echo -n "Git commit: "
	@git rev-parse --short HEAD 2>/dev/null || echo "N/A"
	@echo -n "Git branch: "
	@git branch --show-current 2>/dev/null || echo "N/A"

quick: build up open ## Quick start: build, start, and open browser
	@echo "$(GREEN)🌺 Shoghi Platform is ready!$(NC)"
