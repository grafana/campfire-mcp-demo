# Python executable - use uv run if in uv project, otherwise system python
PYTHON := $(shell if [ -f pyproject.toml ]; then echo "uv run python"; else echo python; fi)

.PHONY: help install start stop restart logs clean demo

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install Python dependencies using uv
	uv sync
	@echo "Dependencies installed with uv!"

setup-dev: install ## Setup development environment (alias for install)
	@echo "Development environment ready!"

start: ## Start all services (Prometheus, Grafana, and the app)
	@echo "Starting Docker services..."
	docker-compose up -d
	@echo "Waiting for services to be ready..."
	sleep 10
	@echo "Starting the metrics application..."
	$(PYTHON) app.py &
	@echo "All services started!"
	@echo "Access points:"
	@echo "  - Metrics App: http://localhost:8000"
	@echo "  - Prometheus:  http://localhost:9090"
	@echo "  - Grafana:     http://localhost:3000 (admin/admin)"

start-infra: ## Start only Docker services (Prometheus and Grafana)
	docker-compose up -d
	@echo "Infrastructure started. Run 'make start-app' to start the metrics application."

start-app: ## Start only the metrics application
	$(PYTHON) app.py

stop: ## Stop all services
	@echo "Stopping Docker services..."
	docker-compose down
	@echo "Killing any running Python processes..."
	-pkill -f "python app.py" 2>/dev/null || true
	@echo "All services stopped!"

restart: stop start ## Restart all services

logs: ## Show logs from Docker services
	docker-compose logs -f

logs-prometheus: ## Show Prometheus logs
	docker-compose logs -f prometheus

logs-grafana: ## Show Grafana logs
	docker-compose logs -f grafana

status: ## Show status of all services
	@echo "Docker services:"
	docker-compose ps
	@echo ""
	@echo "Application endpoints:"
	@curl -s http://localhost:8000/health 2>/dev/null && echo "✓ Metrics app is running" || echo "✗ Metrics app is not responding"
	@curl -s http://localhost:9090/-/ready 2>/dev/null && echo "✓ Prometheus is running" || echo "✗ Prometheus is not responding"
	@curl -s http://localhost:3000/api/health 2>/dev/null && echo "✓ Grafana is running" || echo "✗ Grafana is not responding"

clean: ## Clean up all data and containers
	docker-compose down -v
	docker system prune -f

demo: ## Run a complete demo scenario
	@echo "Starting demo scenario..."
	@echo "Make sure all services are running first with 'make start'"
	$(PYTHON) scripts/generate_load.py --scenario demo

load-normal: ## Generate normal traffic load
	$(PYTHON) scripts/generate_load.py --scenario normal --duration 300

load-spike: ## Generate traffic spike
	$(PYTHON) scripts/generate_load.py --scenario spike --duration 60

load-errors: ## Generate error patterns
	$(PYTHON) scripts/generate_load.py --scenario errors --duration 180

setup: install start-infra ## Complete setup: install dependencies and start infrastructure
	@echo "Setup complete! Now run 'make start-app' to start the metrics application."

validate: ## Validate that all components are working correctly
	$(PYTHON) scripts/validate_setup.py

quick-start: setup start-app ## Quick start everything
	@echo "Quick start complete! All services are running." 