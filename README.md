# Observability Testing Demo

An example application that generates metrics and logs based on different scenarios to accelerate testing in observability systems. Built with Flask, Prometheus, and Grafana.

## 🚀 Quick Start

```bash
# 1. Setup dependencies
make setup

# 2. Start the stack
make docker-up

# 3. Generate demo traffic
make demo
```

**Access points:**
- **Metrics App**: http://localhost:8000
- **Prometheus**: http://localhost:9090  
- **Grafana**: http://localhost:3000 (admin/admin)

## 📈 Testing Scenarios

The app generates realistic patterns for testing observability tools:

- **Normal traffic** - Steady baseline metrics
- **Traffic spikes** - Load testing scenarios  
- **Error patterns** - Simulate failures and debugging
- **Slow requests** - Performance analysis scenarios

## 🏗️ Architecture

```
Flask App ──→ Prometheus ──→ Grafana
(Port 8000)   (Port 9090)    (Port 3000)
```

## 📊 Available Metrics

- `http_requests_total` - Request counts by endpoint/status
- `active_users_count` - Simulated active users

## 🎛️ Endpoints

| Endpoint | Behavior |
|----------|----------|
| `/` | Normal response |
| `/api/users` | Fast, 5% error rate |
| `/api/load` | Slow processing (1-5s) |
| `/health` | Health check |
| `/metrics` | Prometheus metrics |

## 🧪 Commands

```bash
# Setup
make setup              # Install dependencies
make docker-up          # Start services  
make docker-down        # Stop services

# Testing
make test               # Run integration tests

# Load Generation  
make demo               # Complete demo scenario
make load-normal        # Normal traffic (300s)
make load-spike         # Traffic spike (60s)
make load-errors        # Error patterns (180s)

# Code Quality
make lint-check         # Check code style
make lint-fix           # Fix linting issues
```

## 🛠️ Requirements

- Python 3.11+
- Docker & Docker Compose
- [uv](https://docs.astral.sh/uv/) package manager
