# Python executable - use uv run if in uv project, otherwise system python
PYTHON := $(shell if [ -f pyproject.toml ]; then echo "uv run python"; else echo python; fi)

.PHONY: help setup docker-up docker-down test demo load-normal load-spike load-errors lint-check lint-fix

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Install dependencies with uv
	uv sync --extra dev

docker-up: ## Start Docker Compose services
	docker compose up -d

docker-down: ## Stop Docker Compose services
	docker compose down

test-unit: ## Run unit tests
	$(PYTHON) -m pytest tests/ -v -m "not integration"

test-integration: ## Run integration tests with Docker
	docker compose up -d
	@timeout=60; while [ $$timeout -gt 0 ]; do \
		if curl -s http://localhost:8000/health >/dev/null 2>&1; then break; fi; \
		sleep 2; timeout=$$((timeout-2)); \
	done
	$(PYTHON) -m pytest tests/ -v; \
	test_result=$$?; \
	docker compose down; \
	exit $$test_result

demo: ## Run a complete demo scenario
	$(PYTHON) scripts/generate_load.py --scenario demo

load-normal: ## Generate normal traffic load
	$(PYTHON) scripts/generate_load.py --scenario normal --duration 300

load-spike: ## Generate traffic spike
	$(PYTHON) scripts/generate_load.py --scenario spike --duration 60

load-errors: ## Generate error patterns
	$(PYTHON) scripts/generate_load.py --scenario errors --duration 180

lint-check: ## Run linting check
	uv run ruff check .

lint-fix: ## Run linting and fix issues
	uv run ruff check --fix .